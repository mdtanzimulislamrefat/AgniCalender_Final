'use client';

import { MONTH_NAMES, byKey, fmt, maxEvents, years } from '../lib/data';

// Interactive heatmap: click any month cell to show its detail below.
// Colour = harmonized events (darker = more burning). Outlined cells are
// critical months (events > same-month 2019–2024 average + 1 SD).
export default function Heatmap({ selected, onSelect }) {
  return (
    <div className="heat">
      <table aria-label="Harmonized fire events per month, 2003 to 2024">
        <thead>
          <tr>
            <th scope="col">Year</th>
            {MONTH_NAMES.map((n) => (
              <th key={n} scope="col">{n}</th>
            ))}
            <th scope="col">Total</th>
          </tr>
        </thead>
        <tbody>
          {years.map((y) => {
            let total = 0;
            return (
              <tr key={y}>
                <td className="yr">{y}</td>
                {Array.from({ length: 12 }, (_, i) => {
                  const key = `${y}-${String(i + 1).padStart(2, '0')}`;
                  const m = byKey[key];
                  const v = m ? m.harmonized_event_count : 0;
                  total += v;
                  const a = v / maxEvents;
                  const bg = `rgba(194,65,12,${(0.06 + a * 0.88).toFixed(2)})`;
                  const color = a > 0.45 ? '#fff' : '#1f1a17';
                  const cls = [
                    m && m.critical ? 'crit' : '',
                    selected === key ? 'sel' : '',
                  ].join(' ');
                  return (
                    <td
                      key={key}
                      className={cls}
                      style={{ background: bg, color, padding: 0 }}
                      title={`${y} ${MONTH_NAMES[i]}: ${fmt(v)} events${m && m.anomaly_z != null ? `, z ${m.anomaly_z.toFixed(2)}` : ''}`}
                    >
                      <button
                        type="button"
                        onClick={() => onSelect(key)}
                        aria-label={`${y} ${MONTH_NAMES[i]}: ${fmt(v)} harmonized fire events${m && m.critical ? ', critical month' : ''}`}
                      >
                        {fmt(v)}
                        {m && m.critical ? ' ★' : ''}
                      </button>
                    </td>
                  );
                })}
                <td><b>{fmt(total)}</b></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
