const SEV = {
  high: "bg-red-100 text-red-700 ring-red-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  low: "bg-sky-100 text-sky-700 ring-sky-200",
};
export function SeverityBadge({ severity }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ${SEV[severity] ?? SEV.low}`}>
      {severity === "medium" ? "Med" : severity}
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
  return (
    <span className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS[status] ?? STATUS.OK}`}>
      {status === "FESTIVAL_OVER" ? "Festival over" : status}
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
  return (
    <div className="overflow-x-auto rounded-xl ring-1 ring-ink-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-ink-100 text-xs uppercase tracking-wide text-ink-500">
          <tr>
            {columns.map((c, i) => (
              <th key={i} className={`whitespace-nowrap px-3 ${compact ? "py-1.5" : "py-2"} font-semibold`}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-200">
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((cell, j) => (
                <td key={j} className={`whitespace-nowrap px-3 ${compact ? "py-1.5" : "py-2"} ${j > 0 ? "tabular-nums" : "font-medium"}`}>
                  {cell}
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
          <button onClick={onClose} className="rounded-full p-1.5 text-ink-500 hover:bg-ink-100" aria-label="Close">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
