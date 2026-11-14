import Link from 'next/link';
import { climatology, criticalRows, data, fmt, fmtZ } from '../../lib/data';
import DownloadButtons from '../../components/DownloadButtons';

export const metadata = {
  title: 'Critical periods — AgniCalendar',
  description:
    'Unusual burning months in Bangladesh, 2019–2024, flagged against the monthly climatology. January 2019 (z +1.94) and June 2023 (z +1.80) are the most anomalous.',
};

const busiest = [...climatology].sort((a, b) => (b.mean || 0) - (a.mean || 0));
const quietest = [...climatology].sort((a, b) => (a.mean || 0) - (b.mean || 0));

export default function CriticalPage() {
  return (
    <>
      <header className="hero">
        <div className="wrap">
          <span className="pill">Early warning</span>
          <h1>
            Critical periods <span>— unusual months worth a closer look</span>
          </h1>
          <p>
            A month is “critical” when its harmonized events exceed that month’s
            2019–2024 average by more than one standard deviation. It is a flag
            for responders to check — not a verified emergency.
          </p>
        </div>
      </header>
      <main>
        <section>
          <h2>All {criticalRows.length} critical months, most anomalous first</h2>
          <p className="muted">
            Anomaly z = (events − monthly average 2019–2024) ÷ standard deviation.
            Only 2019–2024 months can be critical: those are the years when all
            three sensors (MODIS, VIIRS S-NPP, VIIRS NOAA-20) were flying, so the
            sensor mix matches the baseline. With only 6 climatology years, the
            standard deviation itself is uncertain.
          </p>
          <table>
            <thead>
              <tr>
                <th>Month</th><th>Events</th><th>Same-month average</th><th>Std</th>
                <th>Anomaly z</th><th>Seen by &gt;1 sensor</th>
              </tr>
            </thead>
            <tbody>
              {criticalRows.map((m) => (
                <tr key={m.year_month}>
                  <td><b>{m.year_month}</b></td>
                  <td>{fmt(m.harmonized_event_count)}</td>
                  <td>{m.climatology_mean.toFixed(1)}</td>
                  <td>{m.climatology_std.toFixed(1)}</td>
                  <td><b>{fmtZ(m.anomaly_z)}</b></td>
                  <td>{(m.overlap_share * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted">
            The five most anomalous are also on the dashboard:{' '}
            {data.top_anomalous_months.map((m) => m.year_month).join(', ')}.
          </p>
          <DownloadButtons />
        </section>

        <section>
          <h2>When to watch</h2>
          <p>
            On the 2019–2024 climatology, the busiest months are{' '}
            <b>{busiest[0].name} ({fmt(Math.round(busiest[0].mean))} events on average)</b>{' '}
            and <b>{busiest[1].name} ({fmt(Math.round(busiest[1].mean))})</b>. The
            quietest are {quietest[0].name} and {quietest[1].name}. Plan extra
            monitoring for <b>March–April</b>, and treat an out-of-season spike as
            unusual even if the number looks small.
          </p>
          <ul>
            <li>
              <b>January 2019 — 1,097 events vs a 589 average (z +1.94).</b> The
              most anomalous month in the window, and a big absolute count, not
              just a relative one.
            </li>
            <li>
              <b>June 2023 — 83 events vs a 38.5 average (z +1.80).</b> June is
              normally quiet. 83 looks small next to April’s thousands, but for
              June it is more than double the average — that is the warning.
            </li>
            <li>
              <b>April 2023 — 4,746 events, the peak month of the whole record.</b>{' '}
              It is also critical (z +1.25): even for April, 2023 was above
              average.
            </li>
            <li>
              <b>October 2023 — 87 events vs a 58.3 average (z +1.51).</b> Another
              out-of-season signal, in a month when burning is normally winding down.
            </li>
          </ul>
          <h3>What “critical” does not mean</h3>
          <ul>
            <li>It does not mean a verified emergency — no ground report, burn-scar or weather data is in this calendar.</li>
            <li>It does not mean the most burning — June 2023 (83 events) is critical while April 2024 (thousands) may not be, because April is always busy.</li>
            <li>It is not a prediction. This calendar is a cleaned historical record. A critical month in the past tells you which months to watch, not what will happen next month.</li>
          </ul>
          <p>
            <Link className="btn" href="/">← Back to the dashboard</Link>
            <Link className="btn ghost" href="/method">How the numbers were made →</Link>
          </p>
        </section>
      </main>
    </>
  );
}
