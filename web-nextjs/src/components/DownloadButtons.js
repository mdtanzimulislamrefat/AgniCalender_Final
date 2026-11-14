'use client';

import { data, downloadCSV } from '../lib/data';

export default function DownloadButtons() {
  return (
    <div>
      <button
        type="button"
        className="btn small"
        onClick={() => downloadCSV('agnicalendar_harmonized_monthly_2003-2024.csv')}
      >
        ⬇ Download monthly table (CSV)
      </button>{' '}
      <a className="btn small ghost" href="/data/harmonized.json" download="harmonized.json">
        ⬇ Download full data (JSON)
      </a>
      <p className="muted small">
        {data.monthly.length} monthly rows, {data.coverage.years[0]}–
        {data.coverage.years[data.coverage.years.length - 1]}. Generated{' '}
        {data.generated_at_utc} (UTC). Source: NASA FIRMS.
      </p>
    </div>
  );
}
