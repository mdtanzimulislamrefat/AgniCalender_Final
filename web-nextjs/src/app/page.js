'use client';

import { useState } from 'react';
import Link from 'next/link';
import { MONTH_FULL, MONTH_NAMES, byKey, data, fmt, fmtZ, years } from '../lib/data';
import Heatmap from '../components/Heatmap';
import MonthDetail from '../components/MonthDetail';
import { ClimatologyChart, YearBars } from '../components/Charts';
import YearCompare from '../components/YearCompare';
import DownloadButtons from '../components/DownloadButtons';

const t = data.totals;

export default function Dashboard() {
  const [selected, setSelected] = useState('2023-04');
  const [mode, setMode] = useState('both'); // both | harmonized | raw
  const [pickYear, setPickYear] = useState(2023);
  const [pickMonth, setPickMonth] = useState(4);

  const jumpToMonth = () => {
    const key = `${pickYear}-${String(pickMonth).padStart(2, '0')}`;
    setSelected(key);
    document.getElementById('month-detail')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <>
      <header className="hero">
        <div className="wrap">
          <span className="pill">NASA Space Apps Challenge 2026</span>
          <span className="pill">Harmonization of MODIS and VIIRS Hot Spots</span>
          <span className="pill">Bangladesh</span>
          <h1>
            AgniCalendar <span>— one fire calendar, not three sensor counts</span>
          </h1>
          <p>
            MODIS and VIIRS have watched Bangladesh burn for 20+ years, but the same
            fire was counted 2–5 times — once per satellite, once per pixel.
            AgniCalendar merges those repeat detections into one harmonized fire
            event, so March–April really can be compared with March–April, year
            after year.
          </p>
        </div>
      </header>

      <main>
        <section aria-label="Headline numbers">
          <h2>The headline, in one line</h2>
          <div className="stats">
            <div className="stat"><b>{fmt(t.raw_detections)}</b><span>raw FIRMS detections, 2003–2024</span></div>
            <div className="stat"><b>{fmt(t.harmonized_events)}</b><span>harmonized fire events after 1 km / 1-day merging</span></div>
            <div className="stat"><b>{t.deduplication_ratio.toFixed(2)}×</b><span>raw detections per event — {fmt(t.detections_removed_by_dedup)} merged away</span></div>
            <div className="stat"><b>{fmt(t.peak_month_events)}</b><span>events in the peak month, {t.peak_month} (April)</span></div>
            <div className="stat"><b>{(t.overlap_share * 100).toFixed(1)}%</b><span>events seen by &gt;1 sensor — {fmt(t.overlap_events)} cross-checked events</span></div>
            <div className="stat"><b>{t.viirs_modis_raw_ratio.toFixed(2)} : 1</b><span>VIIRS : MODIS raw ratio — why raw counts can’t be compared</span></div>
          </div>
          <p>
            From <b>{fmt(t.raw_detections)}</b> raw detections, AgniCalendar produces{' '}
            <b>{fmt(t.harmonized_events)}</b> harmonized events for Bangladesh,
            2003–2024. VIIRS alone reports <b>{t.viirs_modis_raw_ratio.toFixed(2)}×</b>{' '}
            as many detections as MODIS — not because there are 3× as many fires, but
            because its 375 m pixels see smaller fires.
          </p>
          <div className="callout">
            <b>What “harmonized” means here:</b> vegetation detections (NASA FIRMS
            type 0) on the same UTC date whose centres are within <b>1.0 km</b>{' '}
            belong to one fire event, regardless of sensor. FRP is never summed
            across sensors — MODIS pixels are ~1 km, VIIRS pixels ~375 m, so
            summing would double-count the same fire.
          </div>
          <DownloadButtons />
        </section>

        <section aria-label="Harmonized calendar">
          <h2>Harmonized burning activity calendar — events per month</h2>
          <p className="muted">
            Each cell is a <b>harmonized fire event</b>, not a raw pixel count.
            Darker = more burning. Click any cell for its detail. Outlined ★ =
            critical month: more events than that month’s 2019–2024 average + 1
            standard deviation. Anomalies are only shown for 2019–2024, when all
            three sensors were flying.
          </p>
          <div className="controls" aria-label="Jump to a month">
            <label>
              Year{' '}
              <select value={pickYear} onChange={(e) => setPickYear(Number(e.target.value))}>
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </label>
            <label>
              Month{' '}
              <select value={pickMonth} onChange={(e) => setPickMonth(Number(e.target.value))}>
                {MONTH_FULL.map((n, i) => (
                  <option key={n} value={i + 1}>{n}</option>
                ))}
              </select>
            </label>
            <button type="button" className="btn small" onClick={jumpToMonth}>
              Show this month ↓
            </button>
          </div>
          <Heatmap selected={selected} onSelect={setSelected} />
          <p className="muted small">
            Peak month in every one of the 22 years is March or April. The burning
            season is March–April; June–October is usually quiet — so a high June
            or October is unusual even when its absolute count is small.
          </p>
          <div style={{ marginTop: 14 }}>
            <MonthDetail yearMonth={selected} />
          </div>
        </section>

        <section aria-label="Raw versus harmonized by year">
          <h2>Raw detections vs harmonized events, by year</h2>
          <p className="muted small">
            Grey = raw FIRMS detections (the old way — the same fire counted many
            times). Orange = harmonized events. The gap is the double-counting this
            project removes. Yearly totals jump when VIIRS arrives (2013, 2019)
            because VIIRS sees smaller fires MODIS misses — that is sensor
            sensitivity, not proof burning increased.
          </p>
          <div className="controls">
            <span className="toggle" role="group" aria-label="Chart series">
              {[
                ['both', 'Both'],
                ['harmonized', 'Harmonized only'],
                ['raw', 'Raw only'],
              ].map(([v, label]) => (
                <button key={v} type="button" className={mode === v ? 'on' : ''} onClick={() => setMode(v)} aria-pressed={mode === v}>
                  {label}
                </button>
              ))}
            </span>
          </div>
          <YearBars mode={mode} />
        </section>

        <section aria-label="Compare two years">
          <h2>Compare two years</h2>
          <p className="muted">
            Pick any two years and compare their monthly harmonized events side by
            side. Try the peak year 2023 against 2024 — or a MODIS-only year
            against a VIIRS year, and watch the sensor era show up.
          </p>
          <YearCompare />
        </section>

        <section aria-label="Climatology">
          <h2>When does Bangladesh burn? — monthly climatology, 2019–2024</h2>
          <ClimatologyChart />
        </section>

        <section aria-label="Critical periods">
          <h2>Critical periods — the most unusual months</h2>
          <p className="muted">
            Anomaly z = (events − monthly average 2019–2024) ÷ standard deviation.
            “Critical” means events &gt; average + 1 SD. Treat it as a flag for
            responders to check, not a verified emergency — with only 6 climatology
            years, the standard deviation itself is uncertain.
          </p>
          <table>
            <thead>
              <tr><th>Month</th><th>Events</th><th>Same-month average</th><th>Anomaly z</th></tr>
            </thead>
            <tbody>
              {data.top_anomalous_months.map((m) => (
                <tr key={m.year_month}>
                  <td><b>{m.year_month}</b></td>
                  <td>{fmt(m.harmonized_event_count)}</td>
                  <td>{m.climatology_mean.toFixed(1)}</td>
                  <td><b>{fmtZ(m.anomaly_z)}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted">
            All {data.critical_months.length} critical months (2019–2024):{' '}
            {data.critical_months.join(', ')}. June, August and October entries
            are anomalous <i>for their usually quiet month</i> — small absolute
            counts, large relative anomaly.
          </p>
          <p>
            <Link className="btn" href="/critical">See all critical months &amp; early-warning guidance →</Link>
            <Link className="btn ghost" href="/method">How the numbers were made →</Link>
          </p>
        </section>

        <section aria-label="How to use this">
          <h2>How a responder or land manager would use this</h2>
          <ol>
            <li><b>Before the season:</b> look at March–April in the calendar — that is when Bangladesh burns, every year.</li>
            <li><b>During the season:</b> compare this month’s harmonized events with the same month’s 2019–2024 average. Above average + 1 SD = critical, check it.</li>
            <li><b>After the season:</b> do not compare a MODIS-only year (2003–2012) directly with a VIIRS year — the sensors see different fires. Compare within the same sensor era, or use the harmonized events.</li>
          </ol>
          <p className="muted small">
            The Android app and FastAPI backend are in the same repository
            (<code>app/</code> and <code>backend/</code>). This site needs no login,
            no server and no APK. The API also serves the calendar at{' '}
            <code>GET /v1/harmonized/calendar</code>.
          </p>
        </section>
      </main>
    </>
  );
}
