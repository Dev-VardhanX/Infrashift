import { useState } from "react";
import { getAlerts, draftAction } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { Async, EmptyState } from "../components/States.jsx";
import { StatusBadge } from "../components/ui.jsx";
import DraftModal from "../components/DraftModal.jsx";
import { dmon, num, num1 } from "../lib/format.js";

const ACTIONABLE = ["OUT", "CRITICAL", "LOW"];
const BAR = { OUT: "bg-red-600", CRITICAL: "bg-red-500", LOW: "bg-amber-500", OK: "bg-emerald-500", FESTIVAL_OVER: "bg-ink-200" };

export default function Restock() {
  const state = useAsync(getAlerts, []);
  const [picked, setPicked] = useState(new Set());
  const [skus, setSkus] = useState(null);
  const [q, setQ] = useState("");
  const draft = useAsync(() => (skus ? draftAction("purchase_order", skus) : Promise.resolve(null)), [skus]);
  const toggle = (sku) => setPicked((p) => { const n = new Set(p); n.has(sku) ? n.delete(sku) : n.add(sku); return n; });

  return (
    <>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold sm:text-3xl">Stock Manager <span className="hi">स्टॉक</span></h1>
          <p className="text-sm text-ink-500">{state.data ? `Stock levels, supplier orders and festival items. Stock as of ${dmon(state.data.as_of)}.` : " "}</p>
        </div>
        <input className="w-full rounded-xl bg-white px-4 py-2.5 text-sm ring-1 ring-ink-200 sm:w-64" placeholder="Search inventory..." value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search inventory" />
      </div>

      <Async state={state} isEmpty={(d) => !d.items?.length}
        empty={<EmptyState icon="✅" title="Nothing to reorder" hint="Every item has enough cover." />}>
        {(d) => {
          const match = (a) => a.name.toLowerCase().includes(q.toLowerCase());
          const actionable = d.items.filter((a) => ACTIONABLE.includes(a.status));
          const levels = d.items.filter(match);
          const over = d.items.filter((a) => a.status === "FESTIVAL_OVER");
          const all = actionable.length > 0 && actionable.every((a) => picked.has(a.sku));
          const suppliers = Object.entries(actionable.reduce((m, a) => ((m[a.supplier] = (m[a.supplier] ?? 0) + 1), m), {}));
          return (
            <div className="grid gap-6 xl:grid-cols-[1fr_20rem]">
              <div className="space-y-6">
                {/* Suggested AI order list */}
                <section className="rounded-3xl bg-brand-50 p-4 ring-1 ring-brand-100 sm:p-5">
                  <div className="flex items-center gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-white text-lg shadow-sm">✨</span>
                    <div>
                      <h2 className="text-lg font-bold">Suggested AI order list</h2>
                      <p className="text-sm text-ink-700">Based on demand forecasting. Tick items, then draft the order.</p>
                    </div>
                  </div>
                  {actionable.length === 0 ? (
                    <p className="mt-4 rounded-2xl bg-white p-4 text-sm text-ink-500">Nothing needs reordering right now.</p>
                  ) : (
                    <div className="mt-4 overflow-x-auto rounded-2xl bg-white ring-1 ring-ink-200">
                      <table className="w-full text-left text-sm">
                        <thead className="text-xs uppercase tracking-wide text-ink-500">
                          <tr>
                            <th className="w-10 px-3 py-3"><input type="checkbox" className="h-5 w-5 accent-orange-600" checked={all} onChange={() => setPicked(all ? new Set() : new Set(actionable.map((a) => a.sku)))} aria-label="Select all" /></th>
                            <th className="px-3 py-3">Item</th><th className="px-3 py-3 text-right">Stock left</th><th className="px-3 py-3 text-right">Suggested order</th><th className="px-3 py-3">Supplier</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-ink-200">
                          {actionable.map((a) => (
                            <tr key={a.sku} className={picked.has(a.sku) ? "bg-brand-50" : ""}>
                              <td className="px-3 py-3"><input type="checkbox" className="h-5 w-5 accent-orange-600" checked={picked.has(a.sku)} onChange={() => toggle(a.sku)} aria-label={`Select ${a.name}`} /></td>
                              <td className="min-w-[10rem] px-3 py-3 font-semibold">{a.name}</td>
                              <td className="px-3 py-3 text-right font-bold tabular-nums text-red-600">{num(a.stock)} units</td>
                              <td className="px-3 py-3 text-right font-bold tabular-nums text-brand-600">{num(a.suggested_qty)} units</td>
                              <td className="whitespace-nowrap px-3 py-3 text-ink-500">{a.supplier}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-ink-700">{picked.size} of {actionable.length} selected</span>
                    <button className="btn-primary shadow-md" disabled={picked.size === 0} onClick={() => setSkus([...picked])}>🛒 Draft PO ({picked.size})</button>
                  </div>
                </section>

                {/* Inventory levels */}
                <section>
                  <h2 className="mb-3 text-lg font-bold">Inventory levels</h2>
                  <div className="card overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-xs uppercase tracking-wide text-ink-500">
                        <tr><th className="px-5 py-3">Item</th><th className="px-3 py-3">Cover</th><th className="px-3 py-3 text-right">Stock</th><th className="px-5 py-3">Status</th></tr>
                      </thead>
                      <tbody className="divide-y divide-ink-200">
                        {levels.map((a) => {
                          const target = a.lead_time_days + 9; // visual only: bar fills as cover approaches lead time + safety + 7 days
                          const w = Math.max(4, Math.min(100, (a.days_of_cover / target) * 100));
                          return (
                            <tr key={a.sku} className={a.status === "FESTIVAL_OVER" ? "text-ink-500" : ""}>
                              <td className="min-w-[10rem] px-5 py-3"><div className="font-semibold">{a.name}</div><div className="text-xs text-ink-500">{a.seasonal_note ?? a.evidence}</div></td>
                              <td className="min-w-[8rem] px-3 py-3">
                                <div className="h-2 w-28 overflow-hidden rounded-full bg-ink-100"><div className={`h-full rounded-full ${BAR[a.status]}`} style={{ width: `${w}%` }} /></div>
                                <div className="mt-1 text-xs font-semibold tabular-nums">{num1(a.days_of_cover)} days (lead {a.lead_time_days}d)</div>
                              </td>
                              <td className="px-3 py-3 text-right font-semibold tabular-nums">{num(a.stock)}</td>
                              <td className="px-5 py-3"><StatusBadge status={a.status} /></td>
                            </tr>
                          );
                        })}
                        {levels.length === 0 && <tr><td colSpan={4} className="px-5 py-6 text-center text-ink-500">No item matches "{q}".</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>
              </div>

              <aside className="space-y-6">
                <section>
                  <h2 className="mb-3 text-lg font-bold">Suppliers to order from</h2>
                  <div className="card divide-y divide-ink-200">
                    {suppliers.length === 0 && <p className="p-4 text-sm text-ink-500">No pending orders.</p>}
                    {suppliers.map(([name, n]) => (
                      <div key={name} className="flex items-center gap-3 p-4">
                        <span className="grid h-10 w-10 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">{name.split(" ").map((w) => w[0]).join("").slice(0, 2)}</span>
                        <div className="flex-1"><div className="font-bold">{name}</div><div className="text-xs text-ink-500">{n} item{n > 1 ? "s" : ""} to order</div></div>
                      </div>
                    ))}
                  </div>
                </section>
                {over.length > 0 && (
                  <section className="card p-5">
                    <h2 className="font-bold">Festival over, do not reorder</h2>
                    <p className="text-sm text-ink-500">Seasonal items. No alert is raised.</p>
                    <ul className="mt-2 divide-y divide-ink-200 text-sm text-ink-500">
                      {over.map((a) => <li key={a.sku} className="py-2">{a.name}</li>)}
                    </ul>
                  </section>
                )}
              </aside>
            </div>
          );
        }}
      </Async>
      {skus && <DraftModal title="Purchase order drafts" state={draft} onClose={() => setSkus(null)} />}
    </>
  );
}
