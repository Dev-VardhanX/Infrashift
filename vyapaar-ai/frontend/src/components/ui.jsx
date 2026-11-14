import React from "react";
import Icon from "./Icon.jsx";
import { useLang } from "../i18n/index.jsx";

const SEV = {
  high: "bg-red-100 text-red-700 ring-red-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  low: "bg-sky-100 text-sky-700 ring-sky-200",
};

export function SeverityBadge({ severity }) {
  const { t } = useLang();
  const label = severity === "high" ? t("sev_high") : severity === "medium" ? t("sev_medium") : t("sev_low");
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${SEV[severity] ?? SEV.low}`}>
      {label}
    </span>
  );
}

const STATUS = {
  OUT: "bg-red-600 text-white",
  CRITICAL: "bg-red-100 text-red-700 ring-1 ring-red-200",
  LOW: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
  OK: "bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200",
  FESTIVAL_OVER: "bg-ink-100 text-ink-500 ring-1 ring-ink-200",
};

export function StatusBadge({ status }) {
  const { t } = useLang();
  const label =
    status === "OUT"
      ? t("status_out")
      : status === "CRITICAL"
        ? t("status_critical")
        : status === "LOW"
          ? t("status_low")
          : status === "FESTIVAL_OVER"
            ? t("status_festival_over")
            : t("status_ok");
  return (
    <span className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS[status] ?? STATUS.OK}`}>
      {label}
    </span>
  );
}

export function PageHeader({ title, subtitle, right }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-extrabold sm:text-3xl">{title}</h1>
        {subtitle && <p className="text-sm text-ink-500">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

/** Generic evidence/result table. Scrolls sideways on narrow screens instead of breaking layout. */
export function DataTable({ columns, rows, compact }) {
  const { tName } = useLang();
  return (
    <div className="overflow-x-auto rounded-xl ring-1 ring-ink-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-ink-100 text-xs uppercase tracking-wide text-ink-500">
          <tr>
            {columns.map((c, i) => (
              <th key={i} className={`whitespace-nowrap px-3 ${compact ? "py-1.5" : "py-2"} font-semibold`}>
                {tName ? tName(c) : c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-200">
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((cell, j) => (
                <td key={j} className={`whitespace-nowrap px-3 ${compact ? "py-1.5" : "py-2"} ${j > 0 ? "tabular-nums" : "font-medium"}`}>
                  {typeof cell === "string" && tName ? tName(cell) : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Modal({ title, onClose, children }) {
  const { t } = useLang();
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-5 shadow-xl sm:max-w-xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">{title}</h2>
          <button onClick={onClose} className="rounded-full p-1.5 text-ink-500 hover:bg-ink-100" aria-label={t("close")}>
            <Icon name="close" className="h-5 w-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
