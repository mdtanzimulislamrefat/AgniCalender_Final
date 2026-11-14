"""Harmonize MODIS + VIIRS FIRMS hotspot detections into fire events.

Standard library only, so this module runs without the database drivers
(``backend.processing.pipeline`` imports psycopg; this module deliberately
does not import it). Row validation mirrors ``pipeline.normalize`` — same
fields, same confidence rules — and produces the same record shape plus
``fire_type`` from the archive CSVs.

Method (see HARMONIZATION_METHOD.md for the full note)
-------------------------------------------------------
1. Keep only detections inside the requested region (the FIRMS country
   files are already per-country; an optional boundary filter is applied
   when a region is given).
2. FIRMS ``type`` 0 (presumed vegetation fire) is harmonized. Other types
   (1 volcano, 2 static land, 3 offshore) are counted separately in
   ``other_types`` and never silently dropped.
3. Spatiotemporal deduplication: vegetation detections on the same UTC
   date whose centres are within 1.0 km of each other belong to ONE
   harmonized fire event, regardless of sensor. One fire seen by MODIS
   and VIIRS counts once, not 2-5 times. Distance is haversine.
4. FRP is reported as max/median *per sensor* inside each event. FRP is
   NEVER summed across sensors: MODIS pixels are ~1 km and VIIRS pixels
   ~375 m, so a summed FRP would mix different pixel sizes and double
   count the same fire.
5. Monthly calendar: per year-month, harmonized event count, raw
   detection count by sensor, overlap share (events seen by >1 sensor),
   median FRP (median over events of each event's max FRP).
6. Climatology uses complete years only, and only years in which every
   requested sensor was present (the harmonization window), so the
   monthly mean/std compare like with like. The current partial year is
   never in the mean. Anomaly z = (events - mean) / std (sample std);
   a month is "critical" when events > mean + 1 SD.

Limitations are carried in every output (see LIMITATIONS).
"""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from backend.paths import BACKEND_DIR, OUTPUT_DIR, RAW_DIR

# FIRMS directory name -> source label used elsewhere in the codebase.
PRODUCTS = {'modis': 'MODIS_ARCHIVE', 'viirs-snpp': 'VIIRS_SNPP_ARCHIVE',
            'viirs-jpss1': 'VIIRS_NOAA20_ARCHIVE'}
# First calendar year with a full twelve months of data for each product
# (same values as backend.storage.archive.FULL_FROM).
FULL_FROM = {'MODIS_ARCHIVE': 2003, 'VIIRS_SNPP_ARCHIVE': 2013, 'VIIRS_NOAA20_ARCHIVE': 2019}
BASE_URL = 'https://firms.modaps.eosdis.nasa.gov/data/country'
CLUSTER_KM = 1.0
EARTH_RADIUS_KM = 6371.0

METHOD = {
    'name': 'Spatiotemporal deduplication into harmonized fire events',
    'clustering': 'Vegetation detections (FIRMS type 0) on the same UTC date '
                  'whose centres are within 1.0 km (haversine) belong to one event, '
                  'regardless of sensor (MODIS / VIIRS S-NPP / VIIRS NOAA-20).',
    'why_1km_1day': 'MODIS pixels are ~1 km and VIIRS pixels ~375 m, so the same '
                    'fire is reported at slightly different centres by each sensor; '
                    '1 km absorbs that geolocation/pixel offset without merging '
                    'neighbouring fires in most of Bangladesh. One UTC day matches '
                    'the FIRMS daily overpass cycle and the way the archive files '
                    'are organised; a fire burning across midnight is split, which '
                    'is a known, stated limitation.',
    'frp': 'Max/median FRP reported per sensor within each event. FRP is never '
           'summed across sensors (different pixel sizes) or across events.',
    'fire_types': 'Only FIRMS type 0 (presumed vegetation fire) is harmonized. '
                  'Types 1 (volcano), 2 (static land) and 3 (offshore) are counted '
                  'separately as other_types and excluded from event counts.',
    'climatology': 'Monthly mean/std computed over complete years only, and only '
                   'over years in which every requested sensor was present (the '
                   'harmonization window). The current partial year is never in '
                   'the mean. Anomaly z = (events - climatology mean) / sample std; '
                   'critical when events > mean + 1 SD. Anomalies are reported only '
                   'for months inside the harmonization window, where the sensor mix '
                   'matches the baseline; earlier years get no anomaly rather than a '
                   'misleading one.',
    'median_frp': 'Monthly median FRP is the median over events of each event\'s '
                  'maximum FRP (any sensor). Per-sensor medians are of detection FRP.',
}

LIMITATIONS = [
    'Detections are thermal-anomaly pixels, not distinct fires, burned area, or fire severity.',
    '1 km / 1 UTC day clustering is an approximation: a large fire can span several events, '
    'and two nearby fires on the same day can be merged into one.',
    'A fire burning across midnight UTC is split into two events (one per day).',
    'VIIRS (375 m) detects smaller/cooler fires that MODIS (1 km) misses, so harmonized '
    'counts are still a lower bound on real fire activity, and the sensor mix changes over time.',
    'No cross-sensor FRP calibration is claimed; FRP is never summed across sensors.',
    'Cloud cover, smoke and overpass timing create gaps; a month with no detections is not '
    'evidence of no fire.',
    'Monthly means span FIRMS processing versions (e.g. MODIS 6.2, 6.03, 61.03), which may '
    'differ slightly in detection.',
    'Counts before a sensor\'s first full year are not comparable with later years; '
    'climatology uses the harmonization window only (years with every sensor present).',
]

FIRE_TYPE_NAMES = {0: 'vegetation', 1: 'volcano', 2: 'static_land', 3: 'offshore'}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def normalize_row(row, source):
    """Validate one FIRMS archive row; same record shape as pipeline.normalize.

    Raises ValueError on any bad field. ``fire_type`` comes from the archive
    ``type`` column (0 vegetation, 1 volcano, 2 static land, 3 offshore).
    """
    lat, lon = float(row['latitude']), float(row['longitude'])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('invalid coordinate')
    day = date.fromisoformat(row['acq_date'].strip())
    time = row['acq_time'].strip().zfill(4)
    if len(time) != 4 or not time.isdigit():
        raise ValueError('invalid time')
    stamp = datetime(day.year, day.month, day.day, int(time[:2]), int(time[2:]), tzinfo=timezone.utc)
    instrument = row.get('instrument', source.split('_')[0]).strip().upper()
    if instrument not in ('MODIS', 'VIIRS') or not source.startswith(instrument):
        raise ValueError('source/instrument mismatch')
    satellite = row['satellite'].strip()
    version = row['version'].strip()
    if not satellite or not version:
        raise ValueError('missing provenance')
    confidence = row['confidence'].strip().lower()
    if instrument == 'MODIS':
        number = float(confidence)
        if not 0 <= number <= 100:
            raise ValueError('invalid MODIS confidence')
        quality = 'low' if number < 30 else 'nominal' if number < 80 else 'high'
    else:
        quality = {'l': 'low', 'n': 'nominal', 'h': 'high',
                   'low': 'low', 'nominal': 'nominal', 'high': 'high'}.get(confidence)
        if quality is None:
            raise ValueError('invalid VIIRS confidence')
    frp = row.get('frp', '').strip()
    frp = float(frp) if frp else None
    if frp is not None and (not math.isfinite(frp) or frp < 0):
        raise ValueError('invalid FRP')
    fire_type = int(row['type'].strip())
    if fire_type not in FIRE_TYPE_NAMES:
        raise ValueError('invalid type')
    return dict(latitude=lat, longitude=lon, timestamp_utc=stamp.isoformat(),
                source=source, instrument=instrument, satellite=satellite,
                version=version, quality=quality, confidence_raw=confidence,
                frp_mw=frp, daynight=row.get('daynight', '').strip(),
                fire_type=fire_type)


def parse_csv(data, source):
    """Validate one yearly FIRMS CSV. Returns (records, stats); bad rows counted, never guessed."""
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    required = {'latitude', 'longitude', 'acq_date', 'acq_time', 'satellite', 'confidence', 'version', 'type'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Not a FIRMS archive CSV: required columns missing')
    stats = {'rows_read': 0, 'retained': 0, 'invalid': 0, 'exact_duplicates': 0}
    seen, records = set(), []
    for row in reader:
        stats['rows_read'] += 1
        try:
            record = normalize_row(row, source)
        except (ValueError, TypeError, AttributeError):
            stats['invalid'] += 1
            continue
        identity = json.dumps(row, sort_keys=True)
        if identity in seen:
            stats['exact_duplicates'] += 1
            continue
        seen.add(identity)
        records.append(record)
        stats['retained'] += 1
    return records, stats


def _cluster_one_day(detections):
    """Union-find clustering of one UTC day's detections within CLUSTER_KM.

    Grid-bucketed (0.01 deg cells, 3x3 neighbourhood) so this stays fast on
    ~10^5 detections; every candidate pair is still checked with haversine.
    """
    n = len(detections)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    cell = 0.01
    grid = defaultdict(list)
    for i, d in enumerate(detections):
        grid[(int(d['latitude'] // cell), int(d['longitude'] // cell))].append(i)
    for i, d in enumerate(detections):
        cx, cy = int(d['latitude'] // cell), int(d['longitude'] // cell)
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for j in grid.get((gx, gy), ()):  # candidates in neighbouring cells
                    if j <= i:
                        continue
                    other = detections[j]
                    if haversine_km(d['latitude'], d['longitude'],
                                    other['latitude'], other['longitude']) <= CLUSTER_KM:
                        union(i, j)
    groups = defaultdict(list)
    for i, d in enumerate(detections):
        groups[find(i)].append(d)
    return list(groups.values())


def harmonize_events(records, fire_types=(0,)):
    """Deduplicate normalized detections into harmonized fire events.

    Returns (events, other_type_counts): ``events`` only covers the requested
    fire types (default vegetation, type 0); ``other_type_counts`` counts every
    other type by name, so nothing is silently dropped.
    """
    other_types = Counter()
    by_day = defaultdict(list)
    for record in records:
        if record['fire_type'] in fire_types:
            by_day[record['timestamp_utc'][:10]].append(record)
        else:
            other_types[FIRE_TYPE_NAMES[record['fire_type']]] += 1
    events = []
    for day, detections in sorted(by_day.items()):
        for group in _cluster_one_day(detections):
            sensors = sorted({d['instrument'] for d in group})
            frp_by_sensor = {}
            for sensor in sensors:
                values = sorted(d['frp_mw'] for d in group
                                if d['instrument'] == sensor and d['frp_mw'] is not None)
                if values:
                    frp_by_sensor[sensor] = {
                        'max_mw': values[-1],
                        'median_mw': statistics.median(values),
                        'n': len(values),
                    }
            all_frp = [d['frp_mw'] for d in group if d['frp_mw'] is not None]
            events.append({
                'date': day,
                'latitude': round(statistics.fmean(d['latitude'] for d in group), 5),
                'longitude': round(statistics.fmean(d['longitude'] for d in group), 5),
                'sensors': sensors,
                'satellites': sorted({d['satellite'] for d in group}),
                'detection_count': len(group),
                'n_pixels': len(group),
                'frp_by_sensor_mw': frp_by_sensor,
                'max_frp_mw': max(all_frp) if all_frp else None,
                'daynight': sorted({d['daynight'] for d in group if d['daynight']}),
                'first_seen_utc': min(d['timestamp_utc'] for d in group),
                'last_seen_utc': max(d['timestamp_utc'] for d in group),
            })
    events.sort(key=lambda e: (e['date'], e['latitude'], e['longitude']))
    return events, dict(other_types)


def monthly_calendar(events, records, years, complete_years):
    """Aggregate events + raw detections into a monthly harmonized calendar.

    ``years`` are the years with data (a month with no events counts as 0,
    not missing); ``complete_years`` are the climatology years. Anomaly z
    uses the sample std of the complete years for that calendar month.
    """
    raw_by_ym_sensor = defaultdict(Counter)
    for r in records:
        raw_by_ym_sensor[(int(r['timestamp_utc'][:4]), int(r['timestamp_utc'][5:7]))][r['instrument']] += 1
    by_ym = defaultdict(list)
    for event in events:
        by_ym[(int(event['date'][:4]), int(event['date'][5:7]))].append(event)
    # Climatology per calendar month over complete years only.
    clim = {}
    for month in range(1, 13):
        values = [len(by_ym.get((y, month), [])) for y in complete_years]
        if len(values) >= 2:
            mean = statistics.fmean(values)
            std = statistics.stdev(values)
        elif values:
            mean, std = float(values[0]), None
        else:
            mean, std = None, None
        clim[month] = {'mean': mean, 'std': std, 'n_years': len(values)}
    rows = []
    for year in sorted(years):
        for month in range(1, 13):
            month_events = by_ym.get((year, month), [])
            count = len(month_events)
            overlap = sum(1 for e in month_events if len(e['sensors']) > 1)
            max_frps = [e['max_frp_mw'] for e in month_events if e['max_frp_mw'] is not None]
            # Anomalies are only meaningful where the sensor mix matches the
            # climatology: years inside the harmonization window. Earlier years
            # (fewer sensors) would look artificially quiet against a later
            # baseline, so they get no anomaly rather than a misleading one.
            in_window = year in complete_years
            c = clim[month] if in_window else {'mean': None, 'std': None}
            anomaly = None
            if c['mean'] is not None and c['std']:
                anomaly = round((count - c['mean']) / c['std'], 2)
            elif c['mean'] is not None and c['std'] == 0.0:
                anomaly = 0.0 if count == c['mean'] else None
            critical = bool(c['mean'] is not None and c['std'] and count > c['mean'] + c['std'])
            rows.append({
                'year': year, 'month': month, 'year_month': f'{year}-{month:02d}',
                'harmonized_event_count': count,
                'raw_detection_count': sum(raw_by_ym_sensor[(year, month)].values()),
                'raw_detection_count_by_sensor': {
                    s: raw_by_ym_sensor[(year, month)][s] for s in ('MODIS', 'VIIRS')},
                'overlap_events': overlap,
                'overlap_share': round(overlap / count, 3) if count else 0.0,
                'median_frp_mw': round(statistics.median(max_frps), 2) if max_frps else None,
                'climatology_mean': round(c['mean'], 1) if c['mean'] is not None else None,
                'climatology_std': round(c['std'], 1) if c['std'] is not None else None,
                'anomaly_z': anomaly,
                'critical': critical,
            })
    return rows


def build_calendar(records, years, products_present, generated_at=None):
    """Full harmonized calendar document from normalized records.

    ``products_present`` maps source label -> sorted list of years with a file.
    The harmonization window is the years where every requested product has
    a file; climatology uses the complete years inside that window.
    """
    current_year = (datetime.now(timezone.utc)).year
    window = sorted(set.intersection(*(set(y) for y in products_present.values()))) if products_present else []
    complete_years = [y for y in window
                      if all(y >= FULL_FROM[s] for s in products_present) and y < current_year]
    events, other_types = harmonize_events(records)
    monthly = monthly_calendar(events, records, sorted(years), complete_years)
    raw_by_sensor = Counter(r['instrument'] for r in records)
    raw_total = len(records)
    veg_total = sum(1 for r in records if r['fire_type'] == 0)
    overlap_events = sum(1 for e in events if len(e['sensors']) > 1)
    anomalous = sorted((r for r in monthly if r['anomaly_z'] is not None),
                       key=lambda r: r['anomaly_z'], reverse=True)
    peak = max(monthly, key=lambda r: r['harmonized_event_count']) if monthly else None
    totals = {
        'raw_detections': raw_total,
        'raw_detections_by_sensor': {s: raw_by_sensor[s] for s in ('MODIS', 'VIIRS')},
        'vegetation_detections': veg_total,
        'other_types': other_types,
        'harmonized_events': len(events),
        'overlap_events': overlap_events,
        'overlap_share': round(overlap_events / len(events), 3) if events else 0.0,
        'deduplication_ratio': round(raw_total / len(events), 2) if events else None,
        'detections_removed_by_dedup': raw_total - len(events),
        'viirs_modis_raw_ratio': (round(raw_by_sensor['VIIRS'] / raw_by_sensor['MODIS'], 2)
                                  if raw_by_sensor['MODIS'] else None),
        'peak_month': peak['year_month'] if peak else None,
        'peak_month_events': peak['harmonized_event_count'] if peak else None,
    }
    return {
        'schema_version': 1,
        'region': 'Bangladesh',
        'timezone': 'UTC',
        'generated_at_utc': generated_at or datetime.now(timezone.utc).isoformat(),
        'method': METHOD,
        'limitations': LIMITATIONS,
        'coverage': {
            'products': {s: {'years': ys, 'first_full_year': FULL_FROM.get(s)}
                         for s, ys in sorted(products_present.items())},
            'years': sorted(years),
            'harmonization_window': [window[0], window[-1]] if window else None,
            'complete_years_for_climatology': complete_years,
            'current_year_excluded_from_climatology': current_year,
        },
        'totals': totals,
        'monthly': monthly,
        'top_anomalous_months': [
            {k: r[k] for k in ('year_month', 'harmonized_event_count', 'climatology_mean',
                               'climatology_std', 'anomaly_z', 'critical', 'overlap_share')}
            for r in anomalous[:5]],
        'critical_months': [r['year_month'] for r in monthly if r['critical']],
    }


# ---------------------------------------------------------------- downloads

def file_url(product, year, country='Bangladesh'):
    return f'{BASE_URL}/{product}/{year}/{product}_{year}_{country}.csv'


def download_file(url, timeout=120):
    """Return bytes, or None on 404 (file not published). Other errors raise."""
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except URLError:
        raise


def download_years(products, years, country, raw_dir, workers=8):
    """Download yearly FIRMS files in parallel; cache-aware and resumable.

    Existing non-empty files with a valid FIRMS header are reused (no
    re-download). Returns (files, unavailable): files maps
    (product, year) -> Path, unavailable lists (product, year) that 404'd.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for product in products:
        for year in years:
            if year < FULL_FROM[PRODUCTS[product]]:
                continue
            target = raw_dir / f'{product}_{year}_{country}.csv'
            if target.exists() and target.stat().st_size > 0:
                first = target.open('rb').readline()
                if first.startswith(b'latitude,'):
                    jobs.append((product, year, target, None))  # cached
                    continue
            jobs.append((product, year, target, file_url(product, year, country)))
    files, unavailable = {}, []
    todo = [(p, y, t, u) for p, y, t, u in jobs if u is not None]
    cached = [(p, y, t) for p, y, t, u in jobs if u is None]

    def fetch(job):
        product, year, target, url = job
        data = download_file(url)
        if data is None:
            return product, year, target, 'unavailable'
        if not data.startswith(b'latitude,'):
            raise ValueError(f'{url} did not return a FIRMS CSV')
        tmp = target.with_suffix('.csv.tmp')
        tmp.write_bytes(data)
        tmp.replace(target)
        return product, year, target, 'downloaded'

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for product, year, target, status in pool.map(fetch, todo):
            if status == 'unavailable':
                unavailable.append((product, year))
            else:
                files[(product, year)] = target
    for product, year, target in cached:
        files[(product, year)] = target
    return files, sorted(unavailable)


def year_range(text):
    first, _, last = text.partition('-')
    first, last = int(first), int(last or first)
    if not 2000 <= first <= last <= 2100:
        raise argparse.ArgumentTypeError('Use YEAR or FIRST-LAST between 2000 and 2100')
    return range(first, last + 1)


def main():
    parser = argparse.ArgumentParser(
        description='Harmonize MODIS + VIIRS FIRMS detections into a burning activity calendar.',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--years', type=year_range, default=year_range('2013-2024'),
                        help='Year or FIRST-LAST (default 2013-2024, the MODIS+VIIRS overlap window)')
    parser.add_argument('--products', default='modis,viirs-snpp,viirs-jpss1',
                        help='Comma list of ' + ', '.join(PRODUCTS))
    parser.add_argument('--country', default='Bangladesh')
    parser.add_argument('--raw-dir', type=Path, default=RAW_DIR)
    parser.add_argument('--output', type=Path, default=OUTPUT_DIR / 'harmonized_monthly.json')
    parser.add_argument('--web-output', type=Path, default=BACKEND_DIR.parent / 'web' / 'data' / 'harmonized.json')
    parser.add_argument('--no-download', action='store_true',
                        help='Use only CSVs already in --raw-dir; do not fetch missing years')
    parser.add_argument('--no-web-output', action='store_true', help='Skip writing the web JSON')
    args = parser.parse_args()
    products = args.products.split(',')
    if unknown := set(products) - set(PRODUCTS):
        parser.error(f'Unknown products: {", ".join(sorted(unknown))}')
    if args.no_download:
        files, unavailable = {}, []
        for product in products:
            for year in args.years:
                if year < FULL_FROM[PRODUCTS[product]]:
                    continue  # sensor did not exist yet; not "unavailable"
                target = args.raw_dir / f'{product}_{year}_{args.country}.csv'
                if target.exists() and target.stat().st_size > 0:
                    files[(product, year)] = target
                else:
                    unavailable.append((product, year))
    else:
        try:
            files, unavailable = download_years(products, args.years, args.country, args.raw_dir)
        except (ValueError, OSError) as exc:
            parser.exit(1, f'Download failed: {exc}\n')
    if not files:
        parser.exit(1, 'No FIRMS files available; nothing to harmonize.\n')
    records, products_present, manifest = [], defaultdict(list), {}
    for (product, year), path in sorted(files.items()):
        source = PRODUCTS[product]
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        try:
            parsed, stats = parse_csv(data, source)
        except ValueError as exc:
            print(f'SKIP {path.name}: {exc}')
            continue
        records.extend(parsed)
        products_present[source].append(year)
        manifest[f'{product}/{year}'] = {'file': str(path), 'sha256': digest, **stats}
        print(f'{source} {year}: {stats["retained"]} kept, {stats["invalid"]} invalid, '
              f'sha256 {digest[:12]}', flush=True)
    for product, year in unavailable:
        print(f'UNAVAILABLE {product} {year}: FIRMS has not published this file (404)')
    years = sorted({y for _, y in files})
    document = build_calendar(records, years, {s: sorted(v) for s, v in products_present.items()})
    document['inputs'] = manifest
    document['unavailable'] = [f'{p}/{y}' for p, y in unavailable]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + '\n')
    print(f'Wrote {args.output}')
    if not args.no_web_output:
        web_doc = {
            'schema_version': 1,
            'region': 'Bangladesh',
            'generated_at_utc': document['generated_at_utc'],
            'method_summary': METHOD['clustering'] + ' ' + METHOD['frp'],
            'limitations': LIMITATIONS,
            'coverage': document['coverage'],
            'totals': document['totals'],
            'monthly': document['monthly'],
            'top_anomalous_months': document['top_anomalous_months'],
            'critical_months': document['critical_months'],
        }
        args.web_output.parent.mkdir(parents=True, exist_ok=True)
        args.web_output.write_text(json.dumps(web_doc, indent=2) + '\n')
        print(f'Wrote {args.web_output}')
    t = document['totals']
    print(f"Years: {document['coverage']['years']}; window: {document['coverage']['harmonization_window']}; "
          f"raw detections: {t['raw_detections']}; harmonized events: {t['harmonized_events']}; "
          f"dedup ratio: {t['deduplication_ratio']}; peak month: {t['peak_month']} "
          f"({t['peak_month_events']} events)")


if __name__ == '__main__':
    main()
