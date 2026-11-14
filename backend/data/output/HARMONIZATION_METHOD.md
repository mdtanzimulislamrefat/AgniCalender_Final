# Harmonization method — AgniCalendar burning activity calendar

**Region:** Bangladesh (FIRMS country files). **Timezone:** UTC. **Generated from real
NASA FIRMS yearly country files** — no invented numbers. Reproduce with:

```bash
python -m backend.processing.harmonize --years 2003-2024 --products modis,viirs-snpp,viirs-jpss1
```

Cached CSVs in `backend/data/raw/` are reused (SHA-256 recorded in
`backend/data/output/harmonized_monthly.json` under `inputs`); missing years are
downloaded in parallel, 404s recorded as unavailable, never fabricated.

## What "harmonized" means here

The old pipeline kept MODIS and VIIRS separate because the same fire is reported
several times: by Terra and Aqua (MODIS), by S-NPP and NOAA-20 (VIIRS), and as
several adjacent pixels. This module collapses those repeat detections into one
**fire event**:

1. **Vegetation fires only (FIRMS `type` 0)** are harmonized. Types 1 (volcano),
   2 (static land) and 3 (offshore) are counted separately (`other_types`) and
   never silently dropped.
2. **Spatiotemporal deduplication:** vegetation detections on the same UTC date
   whose centres are within **1.0 km** (haversine) belong to one event,
   regardless of sensor. One fire seen by MODIS + VIIRS counts once, not 2–5 times.
3. **FRP is never summed across sensors.** Each event records max/median FRP
   *per sensor*. MODIS pixels are ~1 km and VIIRS pixels ~375 m, so summing FRP
   would mix pixel sizes and double-count the same fire.
4. Each event records date, centroid lat/lon, sensors and satellites seen,
   detection count (= pixels), per-sensor FRP, and day/night.
5. **Monthly calendar:** per year-month — harmonized event count, raw detection
   count by sensor, overlap share (events seen by >1 sensor / all events),
   median FRP (median over events of each event's max FRP).
6. **Climatology:** monthly mean/std over **complete years only, inside the
   harmonization window** (years where every requested sensor was present).
   The current partial year is never in the mean. Anomaly
   z = (events − mean) / sample std; a month is **critical** when
   events > mean + 1 SD. Anomalies are reported only for months inside the
   window, where the sensor mix matches the baseline — earlier years get no
   anomaly rather than a misleading one.

## Why 1 km / 1 day

MODIS pixels are ~1 km and VIIRS ~375 m, so the same fire is reported at slightly
different centres by each sensor; 1 km absorbs that geolocation/pixel offset
without merging neighbouring fires in most of Bangladesh. One UTC day matches the
FIRMS daily overpass cycle and the archive files' organisation. A fire burning
across midnight UTC is split into two events — a known, stated limitation.

## Results (real FIRMS data, 2003–2024)

| | |
|---|---|
| Yearly files used | MODIS 2003–2024 (22), VIIRS S-NPP 2013–2024 (12), VIIRS NOAA-20 2019–2024 (6); 40 files, 0 unavailable, 0 invalid rows |
| Raw detections | **244,308** (MODIS 60,141; VIIRS 184,167; VIIRS:MODIS raw ratio **3.06**) |
| Vegetation detections (type 0) | 237,865; other types: static land 5,336, offshore 1,107 (volcano 0) |
| Harmonized fire events | **117,602** |
| Deduplication | 126,706 detections merged away; ratio **2.08 raw detections per event** |
| Events seen by >1 sensor | 8,680 (**7.4%** overall; 10.2% in 2013–2018, 9.5% in 2019–2024; 0% in the MODIS-only era) |
| Peak month | **2023-04: 4,746 events** (from 18,685 raw detections; overlap share 15.7%; median FRP 7.37 MW; April climatology mean 3,887.8, std 689.1, z = +1.25, critical) |
| Harmonization window / climatology years | 2019–2024 (6 complete years, all three sensors) |

By era: 2003–2012 (MODIS only) 28,765 events from 33,204 detections;
2013–2018 (MODIS + S-NPP) 36,401 events from 73,650; 2019–2024 (all sensors)
52,436 events from 137,454. Yearly event counts jump when a sensor is added
(2012: 2,862 → 2013: 7,411; 2018: 5,685 → 2019: 9,732) — that is mostly VIIRS
detecting smaller fires MODIS misses, **not** proof that burning increased.

### Top 5 anomalous months (z-score vs 2019–2024 climatology)

| Month | Events | Climatology mean | Std | z | Critical |
|---|---|---|---|---|---|
| 2019-01 | 1,097 | 589.3 | 261.4 | **+1.94** | yes |
| 2023-06 | 83 | 38.5 | 24.7 | **+1.80** | yes |
| 2021-11 | 419 | 293.2 | 74.0 | **+1.70** | yes |
| 2019-08 | 35 | 22.2 | 8.2 | **+1.56** | yes |
| 2023-10 | 87 | 58.3 | 18.9 | **+1.51** | yes |

All 13 critical months: 2019-01, 2019-03, 2019-08, 2020-02, 2021-11, 2021-12,
2022-07, 2023-04, 2023-05, 2023-06, 2023-07, 2023-09, 2023-10. Note that
2023-06, 2019-08 and 2023-10 are anomalous *for their usually quiet month*
(small absolute counts, large relative anomaly) — read them as "unusual for
June/August/October", not as the worst fire months. March–April is the
dominant burning season: the peak month is March or April in all 22 years.

## Limitations (also embedded in every JSON output)

- Detections are thermal-anomaly pixels, not distinct fires, burned area, or severity.
- 1 km / 1 UTC day clustering is an approximation: a large fire can span several
  events, and two nearby fires on the same day can merge into one.
- VIIRS (375 m) detects smaller/cooler fires MODIS (1 km) misses, so harmonized
  counts are still a lower bound, and the sensor mix changes over time — do not
  read year-to-year changes across sensor eras as calibrated trends.
- No cross-sensor FRP calibration is claimed; FRP is never summed across sensors.
- Cloud cover, smoke and overpass timing create gaps; a month with no detections
  is not evidence of no fire.
- Monthly means span FIRMS processing versions (MODIS 6.2, 6.03, 61.03), which
  may differ slightly in detection.
- With only 6 climatology years, the std — and therefore z — is itself uncertain;
  treat "critical" as "worth a closer look", not a verified emergency.
