import { inr, inrCompact, num, num1, pct } from "../lib/format.js";
import { useLang } from "../i18n/index.jsx";
import Icon from "./Icon.jsx";

const FORMATTERS = { inr, inrCompact, num, num1, pct };

/** KPI tile (UX Pilot style): small caps label, big value, delta chip vs previous period. */
export default function Kpi({ label, value, fmt = "inr", deltaPct, deltaPp, hint, tone }) {
  const { t } = useLang();
  const f = FORMATTERS[fmt] ?? inr;
  const delta = deltaPct ?? deltaPp;
  const unit = deltaPp !== undefined ? " pp" : "%";
  const flat = delta === 0 || delta === undefined || delta === null;
  const up = delta > 0;

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs font-bold uppercase tracking-wide text-ink-500">{label}</div>
      </div>
      <div className={`mt-2 text-2xl font-extrabold tabular-nums ${tone === "danger" ? "text-red-600" : ""}`}>
        {f(value)}
      </div>
      {!flat ? (
        <div className="mt-2 flex items-center gap-1.5 text-xs">
          <span
            className={`inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 font-bold ${
              up ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
            }`}
          >
            <Icon name={up ? "arrow-up" : "arrow-down"} className="h-3 w-3 stroke-[2.5]" />
            <span>
              {Math.abs(delta).toFixed(1)}
              {unit}
            </span>
          </span>
          <span className="text-ink-500">{t("vs_prev_period")}</span>
        </div>
      ) : (
        <div className="mt-2 text-xs font-medium text-ink-500">{hint ?? " "}</div>
      )}
    </div>
  );
}
