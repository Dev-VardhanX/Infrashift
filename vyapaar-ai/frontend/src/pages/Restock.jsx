import { useState } from "react";
import { getAlerts, draftAction } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { Async, EmptyState } from "../components/States.jsx";
import { StatusBadge } from "../components/ui.jsx";
import DraftModal from "../components/DraftModal.jsx";
import Icon from "../components/Icon.jsx";
import { dmon, num, num1 } from "../lib/format.js";
import { useLang } from "../i18n/index.jsx";

const ACTIONABLE = ["OUT", "CRITICAL", "LOW"];
const BAR = {
  OUT: "bg-red-600",
  CRITICAL: "bg-red-500",
  LOW: "bg-amber-500",
  OK: "bg-emerald-500",
  FESTIVAL_OVER: "bg-ink-200",
};

export default function Restock() {
  const { lang, t, tName } = useLang();
  const state = useAsync(getAlerts, []);
  const [picked, setPicked] = useState(new Set());
  const [skus, setSkus] = useState(null);
  const [q, setQ] = useState("");
  const draft = useAsync(() => (skus ? draftAction("purchase_order", skus, lang) : Promise.resolve(null)), [skus, lang]);
  const toggle = (sku) =>
    setPicked((p) => {
      const n = new Set(p);
      n.has(sku) ? n.delete(sku) : n.add(sku);
      return n;
    });

  return (
    <>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold sm:text-3xl">{t("stock_manager_title")}</h1>
          <p className="text-sm text-ink-500">
            {state.data ? t("stock_manager_subtitle", { date: dmon(state.data.as_of) }) : " "}
          </p>
        </div>
        <input
          className="w-full rounded-xl bg-white px-4 py-2.5 text-sm ring-1 ring-ink-200 sm:w-64"
          placeholder={t("search_inventory_placeholder")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label={t("search_inventory_placeholder")}
        />
      </div>

      <Async
        state={state}
        isEmpty={(d) => !d.items?.length}
        empty={<EmptyState icon="check" title={t("nothing_to_reorder_title")} hint={t("nothing_to_reorder_hint")} />}
      >
        {(d) => {
          const match = (a) =>
            a.name.toLowerCase().includes(q.toLowerCase()) ||
            tName(a.name).toLowerCase().includes(q.toLowerCase());
          const actionable = d.items.filter((a) => ACTIONABLE.includes(a.status));
          const levels = d.items.filter(match);
          const over = d.items.filter((a) => a.status === "FESTIVAL_OVER");
          const all = actionable.length > 0 && actionable.every((a) => picked.has(a.sku));
          const suppliers = Object.entries(
            actionable.reduce((m, a) => ((m[a.supplier] = (m[a.supplier] ?? 0) + 1), m), {})
          );
          return (
            <div className="grid gap-6 xl:grid-cols-[1fr_20rem]">
              <div className="space-y-6">
                {/* Suggested AI order list */}
                <section className="rounded-3xl bg-brand-50 p-4 ring-1 ring-brand-100 sm:p-5">
                  <div className="flex items-center gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-white text-brand-600 shadow-sm">
                      <Icon name="sparkle" className="h-5 w-5" />
                    </span>
                    <div>
                      <h2 className="text-lg font-bold">{t("suggested_ai_order_list")}</h2>
                      <p className="text-sm text-ink-700">{t("suggested_ai_order_desc")}</p>
                    </div>
                  </div>
                  {actionable.length === 0 ? (
                    <p className="mt-4 rounded-2xl bg-white p-4 text-sm text-ink-500">
                      {t("nothing_needs_reorder")}
                    </p>
                  ) : (
                    <div className="mt-4 overflow-x-auto rounded-2xl bg-white ring-1 ring-ink-200">
                      <table className="w-full text-left text-sm">
                        <thead className="text-xs uppercase tracking-wide text-ink-500">
                          <tr>
                            <th className="w-10 px-3 py-3">
                              <input
                                type="checkbox"
                                className="h-5 w-5 accent-orange-600"
                                checked={all}
                                onChange={() =>
                                  setPicked(all ? new Set() : new Set(actionable.map((a) => a.sku)))
                                }
                                aria-label={t("select_all")}
                              />
                            </th>
                            <th className="px-3 py-3">{t("col_item")}</th>
                            <th className="px-3 py-3 text-right">{t("col_stock_left")}</th>
                            <th className="px-3 py-3 text-right">{t("col_suggested_order")}</th>
                            <th className="px-3 py-3">{t("col_supplier")}</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-ink-200">
                          {actionable.map((a) => (
                            <tr key={a.sku} className={picked.has(a.sku) ? "bg-brand-50" : ""}>
                              <td className="px-3 py-3">
                                <input
                                  type="checkbox"
                                  className="h-5 w-5 accent-orange-600"
                                  checked={picked.has(a.sku)}
                                  onChange={() => toggle(a.sku)}
                                  aria-label={t("select_item", { name: tName(a.name) })}
                                />
                              </td>
                              <td className="min-w-[10rem] px-3 py-3 font-semibold">{tName(a.name)}</td>
                              <td className="px-3 py-3 text-right font-bold tabular-nums text-red-600">
                                {num(a.stock)} {t("units")}
                              </td>
                              <td className="px-3 py-3 text-right font-bold tabular-nums text-brand-600">
                                {num(a.suggested_qty)} {t("units")}
                              </td>
                              <td className="whitespace-nowrap px-3 py-3 text-ink-500">{tName(a.supplier)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-ink-700">
                      {t("selected_count", { count: picked.size, total: actionable.length })}
                    </span>
                    <button
                      className="btn-primary shadow-md inline-flex items-center gap-2"
                      disabled={picked.size === 0}
                      onClick={() => setSkus([...picked])}
                    >
                      <Icon name="cart" className="h-4 w-4" />
                      <span>{t("draft_po_btn", { count: picked.size })}</span>
                    </button>
                  </div>
                </section>

                {/* Inventory levels */}
                <section>
                  <h2 className="mb-3 text-lg font-bold">{t("inventory_levels")}</h2>
                  <div className="card overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-xs uppercase tracking-wide text-ink-500">
                        <tr>
                          <th className="px-5 py-3">{t("col_item")}</th>
                          <th className="px-3 py-3">{t("col_cover")}</th>
                          <th className="px-3 py-3 text-right">{t("col_stock")}</th>
                          <th className="px-5 py-3">{t("col_status")}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-ink-200">
                        {levels.map((a) => {
                          const target = a.lead_time_days + 9;
                          const w = Math.max(4, Math.min(100, (a.days_of_cover / target) * 100));
                          return (
                            <tr key={a.sku} className={a.status === "FESTIVAL_OVER" ? "text-ink-500" : ""}>
                              <td className="min-w-[10rem] px-5 py-3">
                                <div className="font-semibold">{tName(a.name)}</div>
                                <div className="text-xs text-ink-500">{tName(a.seasonal_note ?? a.evidence)}</div>
                              </td>
                              <td className="min-w-[8rem] px-3 py-3">
                                <div className="h-2 w-28 overflow-hidden rounded-full bg-ink-100">
                                  <div className={`h-full rounded-full ${BAR[a.status]}`} style={{ width: `${w}%` }} />
                                </div>
                                <div className="mt-1 text-xs font-semibold tabular-nums">
                                  {t("days_cover_lead", { days: num1(a.days_of_cover), lead: a.lead_time_days })}
                                </div>
                              </td>
                              <td className="px-3 py-3 text-right font-semibold tabular-nums">{num(a.stock)}</td>
                              <td className="px-5 py-3">
                                <StatusBadge status={a.status} />
                              </td>
                            </tr>
                          );
                        })}
                        {levels.length === 0 && (
                          <tr>
                            <td colSpan={4} className="px-5 py-6 text-center text-ink-500">
                              {t("no_item_matches", { q })}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>
              </div>

              <aside className="space-y-6">
                <section>
                  <h2 className="mb-3 text-lg font-bold">{t("suppliers_to_order_from")}</h2>
                  <div className="card divide-y divide-ink-200">
                    {suppliers.length === 0 && (
                      <p className="p-4 text-sm text-ink-500">{t("no_pending_orders")}</p>
                    )}
                    {suppliers.map(([name, n]) => (
                      <div key={name} className="flex items-center gap-3 p-4">
                        <span className="grid h-10 w-10 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">
                          {name
                            .split(" ")
                            .map((w) => w[0])
                            .join("")
                            .slice(0, 2)}
                        </span>
                        <div className="flex-1">
                          <div className="font-bold">{tName(name)}</div>
                          <div className="text-xs text-ink-500">
                            {n === 1 ? t("items_to_order", { count: n }) : t("items_to_order_plural", { count: n })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
                {over.length > 0 && (
                  <section className="card p-5">
                    <h2 className="font-bold">{t("festival_over_title")}</h2>
                    <p className="text-sm text-ink-500">{t("festival_over_desc")}</p>
                    <ul className="mt-2 divide-y divide-ink-200 text-sm text-ink-500">
                      {over.map((a) => (
                        <li key={a.sku} className="py-2">
                          {tName(a.name)}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </aside>
            </div>
          );
        }}
      </Async>
      {skus && <DraftModal title={t("purchase_order_drafts")} state={draft} onClose={() => setSkus(null)} />}
    </>
  );
}
