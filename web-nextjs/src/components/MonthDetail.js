import { byKey, fmt, fmt1, fmtZ, monthLabel } from '../lib/data';

// Detail panel for one selected month — every number from harmonized.json.
export default function MonthDetail({ yearMonth }) {
  const m = byKey[yearMonth];
  if (!m) return null;
  return (
    <div className="detail" id="month-detail" aria-live="polite">
      <h3>
        {monthLabel(m)} — {fmt(m.harmonized_event_count)} harmonized fire events
        {m.critical ? ' ★ Critical month' : ''}
      </h3>
      <p className="muted small">
        {m.critical
          ? 'Critical = more events than this month’s 2019–2024 average + 1 standard deviation. A flag to check, not a verified emergency.'
          : m.anomaly_z != null
            ? 'Within the 2019–2024 climatology window; not above average + 1 SD.'
            : 'Before 2019 the sensor mix differs from the climatology baseline, so no anomaly is shown rather than a misleading one.'}
      </p>
      <div className="kv">
        <div><b>{fmt(m.harmonized_event_count)}</b><span>harmonized events</span></div>
        <div><b>{fmt(m.raw_detection_count)}</b><span>raw detections (all sensors)</span></div>
        <div><b>{fmt(m.raw_detection_count_by_sensor.MODIS)}</b><span>raw MODIS detections</span></div>
        <div><b>{fmt(m.raw_detection_count_by_sensor.VIIRS)}</b><span>raw VIIRS detections</span></div>
        <div><b>{fmt(m.overlap_events)} ({(m.overlap_share * 100).toFixed(1)}%)</b><span>events seen by &gt;1 sensor</span></div>
        <div><b>{m.median_frp_mw != null ? `${fmt1(m.median_frp_mw)} MW` : '–'}</b><span>median FRP (per-event max)</span></div>
        <div><b>{fmt1(m.climatology_mean)}</b><span>same-month average, 2019–2024</span></div>
        <div><b>{fmt1(m.climatology_std)}</b><span>same-month std. deviation</span></div>
        <div><b>{fmtZ(m.anomaly_z)}</b><span>anomaly z-score</span></div>
      </div>
    </div>
  );
}
