import Link from 'next/link';
import { data } from '../../lib/data';

export const metadata = {
  title: 'Method & limitations — AgniCalendar',
  description:
    'How AgniCalendar harmonizes MODIS and VIIRS FIRMS detections into one burning activity calendar for Bangladesh, and what the numbers cannot say.',
};

const t = data.totals;
const cov = data.coverage;

export default function MethodPage() {
  return (
    <>
      <header className="hero">
        <div className="wrap">
          <span className="pill">Read before you quote a number</span>
          <h1>
            Method &amp; limitations <span>— how the calendar was made</span>
          </h1>
          <p>{data.method_summary}</p>
        </div>
      </header>
      <main>
        <section>
          <h2>The harmonization, step by step</h2>
          <ol>
            <li>
              <b>Vegetation fires only (FIRMS type 0)</b> are harmonized. Other
              types are counted separately and never silently dropped: static land{' '}
              {t.other_types.static_land.toLocaleString('en-US')}, offshore{' '}
              {t.other_types.offshore.toLocaleString('en-US')}, volcano 0.
            </li>
            <li>
              <b>Spatiotemporal deduplication:</b> vegetation detections on the
              same UTC date whose centres are within <b>1.0 km</b> (haversine)
              belong to one event, regardless of sensor. One fire seen by MODIS +
              VIIRS counts once, not 2–5 times.
            </li>
            <li>
              <b>FRP is never summed across sensors.</b> Each event records
              max/median FRP per sensor. MODIS pixels are ~1 km and VIIRS pixels
              ~375 m, so summing FRP would mix pixel sizes and double-count the
              same fire.
            </li>
            <li>
              <b>Monthly calendar:</b> per year-month — harmonized event count, raw
              detection count by sensor, overlap share (events seen by &gt;1 sensor
              / all events), median FRP.
            </li>
            <li>
              <b>Climatology:</b> monthly mean/std over complete years only, inside
              the harmonization window (years where every requested sensor was
              present). The current partial year is never in the mean. Anomaly z =
              (events − mean) / sample std; a month is <b>critical</b> when events
              &gt; mean + 1 SD.
            </li>
          </ol>
          <h3>Why 1 km / 1 day</h3>
          <p>
            MODIS pixels are ~1 km and VIIRS ~375 m, so the same fire is reported
            at slightly different centres by each sensor; 1 km absorbs that
            geolocation/pixel offset without merging neighbouring fires in most of
            Bangladesh. One UTC day matches the FIRMS daily overpass cycle and the
            archive files’ organisation.
          </p>
          <h3>Coverage actually used</h3>
          <ul>
            <li>MODIS: {cov.products.MODIS_ARCHIVE.years[0]}–{cov.products.MODIS_ARCHIVE.years.slice(-1)[0]} (22 yearly files)</li>
            <li>VIIRS S-NPP: {cov.products.VIIRS_SNPP_ARCHIVE.years[0]}–{cov.products.VIIRS_SNPP_ARCHIVE.years.slice(-1)[0]} (12 files)</li>
            <li>VIIRS NOAA-20: {cov.products.VIIRS_NOAA20_ARCHIVE.years[0]}–{cov.products.VIIRS_NOAA20_ARCHIVE.years.slice(-1)[0]} (6 files)</li>
            <li>40 files, 0 unavailable, 0 invalid rows. Harmonization window / climatology years: {cov.harmonization_window[0]}–{cov.harmonization_window[1]}.</li>
          </ul>
          <pre>{`python -m backend.processing.harmonize --years 2003-2024 --products modis,viirs-snpp,viirs-jpss1`}</pre>
          <p className="muted small">
            Full method note with the exact numbers:{' '}
            <code>backend/data/output/HARMONIZATION_METHOD.md</code> in the repo.
          </p>
        </section>

        <section>
          <h2>The sensor-era warning</h2>
          <p>
            Yearly event counts jump when a sensor is added (2012: 2,862 → 2013:
            7,411; 2018: 5,685 → 2019: 9,732) — that is mostly VIIRS detecting
            smaller fires MODIS misses, <b>not</b> proof that burning increased.
            Do not read year-to-year changes across sensor eras as calibrated
            trends. Compare within the same sensor era, or use the harmonized
            events and the climatology window.
          </p>
          <h2>Limitations</h2>
          <ul>
            {data.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
            <li>2025–2026 yearly files are not published by NASA yet, so they are not in this calendar.</li>
            <li>With only 6 climatology years, the std — and therefore z — is itself uncertain; treat “critical” as “worth a closer look”, not a verified emergency.</li>
          </ul>
        </section>

        <section>
          <h2>Data sources</h2>
          <ul>
            <li><a href="https://firms.modaps.eosdis.nasa.gov/download/">NASA FIRMS archive</a> — yearly country files for Bangladesh.</li>
            <li><a href="https://firms.modaps.eosdis.nasa.gov/data/active_fire/">NASA FIRMS active-fire feeds</a> — rolling 24-hour MODIS + VIIRS feeds (used by the backend).</li>
            <li><a href="https://firms.modaps.eosdis.nasa.gov/api/">NASA FIRMS API</a> — area API for recent-day windows.</li>
            <li>Bangladesh boundary: Natural Earth 1:10m Admin 0 (public domain).</li>
          </ul>
          <p className="muted small">
            This project uses NASA open data and is not affiliated with or endorsed
            by NASA. No NASA logo, flag or mission identifier is used anywhere in
            this site.
          </p>
          <p>
            <Link className="btn" href="/">← Back to the dashboard</Link>
            <Link className="btn ghost" href="/critical">Critical periods →</Link>
          </p>
        </section>
      </main>
    </>
  );
}
