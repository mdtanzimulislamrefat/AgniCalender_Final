'use client';

import { byYear, climatology, fmt, maxClimMean, maxYearRaw } from '../lib/data';

// Yearly raw vs harmonized bars. `mode` is 'both' | 'harmonized' | 'raw'.
export function YearBars({ mode }) {
  return (
    <div>
      {byYear.map((y) => (
        <div key={y.year}>
          {mode !== 'harmonized' && (
            <div className="bar-row">
              <span className="lbl">{y.year}</span>
              <div className="bar raw" style={{ width: `${(y.raw / maxYearRaw) * 100}%` }} />
              <span className="val">{fmt(y.raw)} raw</span>
            </div>
          )}
          {mode !== 'raw' && (
            <div className="bar-row">
              <span className="lbl">{mode === 'both' ? '' : y.year}</span>
              <div className="bar" style={{ width: `${(y.events / maxYearRaw) * 100}%` }} />
              <span className="val">{fmt(y.events)} harmonized</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// Average harmonized events per calendar month, 2019–2024 climatology.
export function ClimatologyChart() {
  return (
    <div>
      {climatology.map((c) => (
        <div className="bar-row" key={c.month}>
          <span className="lbl">{c.name}</span>
          <div
            className="bar clim"
            style={{ width: `${c.mean ? (c.mean / maxClimMean) * 100 : 0}%` }}
          />
          <span className="val">{c.mean ? `${fmt(Math.round(c.mean))} events / month` : '–'}</span>
        </div>
      ))}
      <p className="muted small">
        Average over the six complete climatology years, 2019–2024, when all
        three sensors were flying. March and April dominate every year.
      </p>
    </div>
  );
}
