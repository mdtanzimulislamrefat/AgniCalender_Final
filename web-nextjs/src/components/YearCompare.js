'use client';

import { useState } from 'react';
import { MONTH_NAMES, byKey, fmt, years } from '../lib/data';

// Compare any two years, month by month. All values from harmonized.json.
export default function YearCompare() {
  const [a, setA] = useState(2023);
  const [b, setB] = useState(2024);
  const rows = MONTH_NAMES.map((name, i) => {
    const ma = byKey[`${a}-${String(i + 1).padStart(2, '0')}`];
    const mb = byKey[`${b}-${String(i + 1).padStart(2, '0')}`];
    return { name, a: ma ? ma.harmonized_event_count : 0, b: mb ? mb.harmonized_event_count : 0 };
  });
  const maxV = Math.max(...rows.flatMap((r) => [r.a, r.b]), 1);
  const totalA = rows.reduce((s, r) => s + r.a, 0);
  const totalB = rows.reduce((s, r) => s + r.b, 0);
  return (
    <div>
      <div className="controls">
        <label>
          Year A{' '}
          <select value={a} onChange={(e) => setA(Number(e.target.value))}>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
        <label>
          Year B{' '}
          <select value={b} onChange={(e) => setB(Number(e.target.value))}>
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
        <span className="muted small">
          Totals: {a} = <b>{fmt(totalA)}</b> events · {b} = <b>{fmt(totalB)}</b> events.
          {a < 2013 || b < 2013
            ? ' Note: years before 2013 are MODIS-only, so compare them with care — VIIRS sees smaller fires MODIS misses.'
            : ''}
        </span>
      </div>
      <table aria-label={`Monthly harmonized events, ${a} versus ${b}`}>
        <thead>
          <tr><th>Month</th><th>{a}</th><th>{b}</th><th>Difference (A − B)</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name}>
              <td>{r.name}</td>
              <td>
                <div className="bar" style={{ width: `${(r.a / maxV) * 100}%`, minWidth: r.a ? 4 : 0 }} />
                {fmt(r.a)}
              </td>
              <td>
                <div className="bar raw" style={{ width: `${(r.b / maxV) * 100}%`, minWidth: r.b ? 4 : 0 }} />
                {fmt(r.b)}
              </td>
              <td>{r.a - r.b >= 0 ? '+' : ''}{fmt(r.a - r.b)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
