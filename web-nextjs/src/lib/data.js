import raw from './harmonized.json';

// Every figure in this app comes from harmonized.json — real NASA FIRMS
// data, computed by backend/processing/harmonize.py. Nothing is invented here.
export const data = raw;
export const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const MONTH_FULL = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export const fmt = (n) =>
  n === null || n === undefined ? '–' : Number(n).toLocaleString('en-US');

export const fmt1 = (n) =>
  n === null || n === undefined ? '–' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });

export const fmtZ = (z) =>
  z === null || z === undefined ? '–' : `${z >= 0 ? '+' : ''}${Number(z).toFixed(2)}`;

export const years = [...new Set(data.monthly.map((m) => m.year))].sort((a, b) => a - b);

export const byKey = Object.fromEntries(data.monthly.map((m) => [m.year_month, m]));

export const maxEvents = Math.max(...data.monthly.map((m) => m.harmonized_event_count));

// Yearly totals, computed from the monthly rows (never hand-entered).
export const byYear = years.map((y) => {
  const rows = data.monthly.filter((m) => m.year === y);
  return {
    year: y,
    events: rows.reduce((s, m) => s + m.harmonized_event_count, 0),
    raw: rows.reduce((s, m) => s + m.raw_detection_count, 0),
  };
});
export const maxYearRaw = Math.max(...byYear.map((y) => y.raw));

// Climatology: one mean/std per calendar month (2019–2024 window).
// climatology_mean is identical for a given month across window years,
// so take the first non-null value per month.
export const climatology = MONTH_NAMES.map((name, i) => {
  const row = data.monthly.find((m) => m.month === i + 1 && m.climatology_mean != null);
  return {
    month: i + 1,
    name,
    mean: row ? row.climatology_mean : null,
    std: row ? row.climatology_std : null,
  };
});
export const maxClimMean = Math.max(...climatology.map((c) => c.mean || 0));

// All critical months (2019–2024 only), most anomalous first.
export const criticalRows = data.monthly
  .filter((m) => m.critical)
  .slice()
  .sort((a, b) => (b.anomaly_z ?? -99) - (a.anomaly_z ?? -99));

export function monthLabel(row) {
  return `${MONTH_FULL[row.month - 1]} ${row.year}`;
}

export function downloadCSV(filename) {
  const header = 'year_month,year,month,harmonized_event_count,raw_detection_count,raw_modis,raw_viirs,overlap_events,overlap_share,median_frp_mw,climatology_mean,climatology_std,anomaly_z,critical';
  const lines = data.monthly.map((m) =>
    [
      m.year_month, m.year, m.month, m.harmonized_event_count, m.raw_detection_count,
      m.raw_detection_count_by_sensor.MODIS, m.raw_detection_count_by_sensor.VIIRS,
      m.overlap_events, m.overlap_share, m.median_frp_mw ?? '',
      m.climatology_mean ?? '', m.climatology_std ?? '', m.anomaly_z ?? '', m.critical,
    ].join(','),
  );
  const blob = new Blob([[header, ...lines].join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
