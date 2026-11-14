// Indian number formatting. Money is INR. Dates are ISO internally, "DD MMM" in the UI.
const grouped = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const grouped1 = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 });

/** 1432103 -> "Rs 14,32,103" */
export function inr(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "-";
  const v = Number(n);
  return `${v < 0 ? "-" : ""}Rs ${grouped.format(Math.abs(v))}`;
}

/** 1432103 -> "Rs 14.3 lakh"; 25000000 -> "Rs 2.5 crore"; below 1 lakh falls back to inr() */
export function inrCompact(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "-";
  const v = Math.abs(Number(n));
  const sign = Number(n) < 0 ? "-" : "";
  if (v >= 1e7) return `${sign}Rs ${grouped1.format(v / 1e7)} crore`;
  if (v >= 1e5) return `${sign}Rs ${grouped1.format(v / 1e5)} lakh`;
  return inr(n);
}

/** Plain number with Indian grouping: 44303 -> "44,303" */
export const num = (n) => (n === null || n === undefined ? "-" : grouped.format(Number(n)));
export const num1 = (n) => (n === null || n === undefined ? "-" : grouped1.format(Number(n)));
export const pct = (n, d = 1) => (n === null || n === undefined ? "-" : `${Number(n).toFixed(d)}%`);

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-11-08" -> "08 Nov" (parsed by hand so the timezone can never shift the day) */
export function dmon(iso) {
  if (!iso) return "-";
  const [, m, d] = String(iso).slice(0, 10).split("-");
  return `${d} ${MONTHS[Number(m) - 1]}`;
}

/** Add days to an ISO date string, returns ISO string. */
export function addDays(iso, days) {
  const [y, m, d] = iso.split("-").map(Number);
  const t = new Date(Date.UTC(y, m - 1, d + days));
  return t.toISOString().slice(0, 10);
}
