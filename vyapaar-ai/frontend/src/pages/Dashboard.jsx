import { useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
  BarChart, Bar, PieChart, Pie, Cell, Legend,
} from "recharts";
import { getDashboard, getInsights, getAlerts, getKhataOverdue } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { go } from "../lib/nav.js";
import { Async, EmptyState } from "../components/States.jsx";
import Kpi from "../components/Kpi.jsx";
import { StatusBadge } from "../components/ui.jsx";
import { inr, inrCompact, dmon, addDays, pct, num } from "../lib/format.js";

const COLORS = ["#ea580c", "#fb923c", "#fdba74", "#fed7aa", "#fff1e0"];
const MODE_LABEL = { upi: "UPI", cash: "Cash", card: "Card", khata: "Khata" };
const RANGES = [{ id: 7, label: "7 Days" }, { id: 30, label: "30 Days" }, { id: "custom", label: "Custom" }];

export default function Dashboard() {
  const [range, setRange] = useState(30);
  const [custom, setCustom] = useState({ from: "", to: "" });
  const [asOf, setAsOf] = useState(null);
  const [topBy, setTopBy] = useState("revenue");

  const params = (() => {
    if (range === "custom") return custom.from && custom.to ? custom : {};
    // 30 days is the backend default, so send no params (avoids a duplicate fetch).
    return asOf && range !== 30 ? { from: addDays(asOf, -(range - 1)), to: asOf } : {};
  })();
  const state = useAsync(() => getDashboard(params).then((d) => (setAsOf((a) => a ?? d.as_of), d)), [params.from, params.to]);

  return (
    <>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold sm:text-3xl">Namaste, Rajesh ji <span className="text-lg font-normal text-ink-500">नमस्ते</span></h1>
          <p className="text-sm text-ink-500">
            {state.data ? `Here's your shop as of ${dmon(state.data.as_of)} (last sale in your data, not today).` : " "}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-xl bg-white p-1 shadow-sm ring-1 ring-ink-200" role="group" aria-label="Date range">
            {RANGES.map((r) => (
              <button key={r.id} onClick={() => setRange(r.id)}
                className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${range === r.id ? "bg-brand-600 text-white" : "text-ink-500"}`}>
                {r.label}
              </button>
            ))}
          </div>
          {range === "custom" && (
            <div className="flex items-center gap-1 text-sm">
              <input type="date" className="rounded-lg bg-white px-2 py-1.5 ring-1 ring-ink-200" value={custom.from} max={custom.to || asOf || undefined}
                onChange={(e) => setCustom((c) => ({ ...c, from: e.target.value }))} aria-label="From date" />
              <span>to</span>
              <input type="date" className="rounded-lg bg-white px-2 py-1.5 ring-1 ring-ink-200" value={custom.to} min={custom.from || undefined} max={asOf || undefined}
                onChange={(e) => setCustom((c) => ({ ...c, to: e.target.value }))} aria-label="To date" />
            </div>
          )}
        </div>
      </div>

      <Async state={state} isEmpty={(d) => !d.series?.daily_revenue?.length}
        empty={<EmptyState icon="🗂️" title="No sales in this period" hint="Pick a different date range, or load your data on the Data tab." />}>
        {(d) => <Body d={d} topBy={topBy} setTopBy={setTopBy} />}
      </Async>
    </>
  );
}

function Body({ d, topBy, setTopBy }) {
  const k = d.kpis;
  const top = topBy === "profit"
    ? d.series.top_products_by_profit ?? [...d.series.top_products].sort((a, b) => b.profit - a.profit)
    : d.series.top_products;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Revenue" hi="कुल बिक्री" value={k.revenue.value} fmt="inrCompact" deltaPct={k.revenue.delta_pct} />
        <Kpi label="Gross profit" hi="मुनाफा" value={k.gross_profit.value} fmt="inrCompact" deltaPct={k.gross_profit.delta_pct} />
        <Kpi label="Pending khata" hi="उधार" value={k.khata_outstanding.value} fmt="inr" tone="danger" hint="Owed by customers" />
        <Kpi label="Stock value" hi="स्टॉक" value={k.stock_value.value} fmt="inr" hint="At cost price" />
        <Kpi label="Gross margin" value={k.gross_margin_pct.value} fmt="pct" deltaPp={k.gross_margin_pct.delta_pp} />
        <Kpi label="Invoices" value={k.invoices.value} fmt="num" deltaPct={k.invoices.delta_pct} />
        <Kpi label="Avg bill" value={k.avg_bill.value} fmt="inr" deltaPct={k.avg_bill.delta_pct} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <InsightCards />
          <Watchlist />
        </div>
        <div className="space-y-6">
          <KhataMini />
          <div className="dark-card">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600/30 text-lg">✨</span>
              <h3 className="text-lg font-bold">Vyapaar AI Buddy</h3>
            </div>
            <p className="mt-3 text-sm text-white/70">Ask about sales, stock or khata in Hindi, Hinglish or English. Every number comes from your data.</p>
            <button className="btn-white mt-4 w-full" onClick={() => go("chat")}>Chat with Vyapaar AI</button>
          </div>
        </div>
      </div>

      <Section title="Revenue performance" hi="कुल आय">
        <div className="h-56 sm:h-72">
          <ResponsiveContainer>
            <LineChart data={d.series.daily_revenue} margin={{ top: 16, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" vertical={false} />
              <XAxis dataKey="date" tickFormatter={dmon} fontSize={11} minTickGap={24} />
              <YAxis tickFormatter={(v) => inrCompact(v).replace("Rs ", "")} fontSize={11} width={52} />
              <Tooltip formatter={(v) => [inr(v), "Revenue"]} labelFormatter={dmon} />
              {d.markers?.filter((m) => m.date >= d.period.from && m.date <= d.period.to).map((m) => (
                <ReferenceLine key={m.date} x={m.date} stroke="#ea580c" strokeDasharray="4 3"
                  label={{ value: `🪔 ${m.label}`, position: "insideTopLeft", fontSize: 11, fill: "#c2410c" }} />
              ))}
              <Line type="monotone" dataKey="revenue" stroke="#ea580c" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Category breakdown">
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={d.series.by_category} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" horizontal={false} />
                <XAxis type="number" tickFormatter={(v) => inrCompact(v).replace("Rs ", "")} fontSize={11} />
                <YAxis type="category" dataKey="category" width={104} fontSize={11} />
                <Tooltip formatter={(v) => [inr(v), "Revenue"]} />
                <Bar dataKey="revenue" fill="#ea580c" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Section>
        <Section title="Payment mix">
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={d.series.payment_mix} dataKey="revenue" nameKey="mode" innerRadius="55%" outerRadius="80%" paddingAngle={2}>
                  {d.series.payment_mix.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v, n, p) => [`${inr(v)} (${pct(p.payload.share_pct)})`, MODE_LABEL[n] ?? n]} />
                <Legend formatter={(m) => `${MODE_LABEL[m] ?? m} ${pct(d.series.payment_mix.find((x) => x.mode === m)?.share_pct)}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Section>
      </div>

      <Section title="Top performing items" right={
        <div className="flex rounded-lg bg-ink-100 p-0.5 text-xs font-semibold" role="group" aria-label="Rank by">
          {["revenue", "profit"].map((m) => (
            <button key={m} onClick={() => setTopBy(m)} className={`rounded-md px-2.5 py-1 capitalize ${topBy === m ? "bg-white shadow-sm" : "text-ink-500"}`}>By {m}</button>
          ))}
        </div>}>
        <ol className="divide-y divide-ink-200">
          {top.map((p, i) => (
            <li key={p.sku} className="flex items-center gap-3 py-2.5">
              <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg text-sm font-bold ${i === 0 ? "bg-brand-100 text-brand-700" : "bg-ink-100 text-ink-500"}`}>#{i + 1}</span>
              <span className="min-w-0 flex-1 truncate font-semibold">{p.name}</span>
              <span className="text-sm text-ink-500">{num(p.units)} units</span>
              <span className="w-24 text-right font-bold tabular-nums">{inr(topBy === "profit" ? p.profit : p.revenue)}</span>
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}

/** Top 2 insights from /insights, styled as the design's "AI Vyapaar Insights" cards. */
function InsightCards() {
  const s = useAsync(getInsights, []);
  const items = s.data ? [...s.data.insights].sort((a, b) => b.impact_inr - a.impact_inr).slice(0, 2) : [];
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-bold">AI Vyapaar Insights <span className="hi">व्यापार सुझाव</span></h2>
        <button className="text-sm font-bold text-brand-600" onClick={() => go("insights")}>See all ›</button>
      </div>
      {s.loading && !s.data ? <div className="card h-40 animate-pulse" /> : s.error ? (
        <div className="card p-4 text-sm text-ink-500">Insights unavailable. <button className="font-bold text-brand-600" onClick={s.reload}>Retry</button></div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {items.map((i, n) => (
            <div key={i.id} className={`rounded-3xl p-5 ring-1 ${n === 0 ? "bg-brand-50 ring-brand-100" : "bg-sky-50 ring-sky-100"}`}>
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-white text-lg shadow-sm">{n === 0 ? "⚠️" : "🎯"}</span>
              <h3 className="mt-3 font-bold leading-snug">{i.title}</h3>
              {i.impact_inr > 0 && <p className="mt-1 text-sm text-ink-700">Impact <b className="text-emerald-700">{inr(i.impact_inr)}</b></p>}
              <button className={`mt-4 rounded-xl px-4 py-2.5 text-sm font-bold text-white ${n === 0 ? "bg-brand-600" : "bg-blue-600"}`} onClick={() => go("insights")}>
                View details
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/** First 3 actionable alerts from /inventory/alerts. */
function Watchlist() {
  const s = useAsync(getAlerts, []);
  const rows = s.data ? s.data.items.filter((a) => ["OUT", "CRITICAL", "LOW"].includes(a.status)).slice(0, 4) : [];
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-bold">Inventory watchlist <span className="hi">स्टॉक लिस्ट</span></h2>
        <button className="text-sm font-bold text-brand-600" onClick={() => go("restock")}>Manage stock</button>
      </div>
      <div className="card overflow-x-auto">
        {s.loading && !s.data ? <div className="h-32 animate-pulse" /> : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-ink-500">
              <tr><th className="px-5 py-3">Item</th><th className="px-3 py-3 text-right">Stock</th><th className="px-3 py-3">Status</th><th className="px-5 py-3 text-right">Action</th></tr>
            </thead>
            <tbody className="divide-y divide-ink-200">
              {rows.map((a) => (
                <tr key={a.sku}>
                  <td className="px-5 py-3"><div className="font-semibold">{a.name}</div><div className="text-xs text-ink-500">SKU: {a.sku}</div></td>
                  <td className="px-3 py-3 text-right font-semibold tabular-nums">{num(a.stock)} units</td>
                  <td className="px-3 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-5 py-3 text-right"><button className="rounded-lg bg-brand-50 px-3 py-1.5 font-bold text-brand-700" onClick={() => go("restock")}>Restock</button></td>
                </tr>
              ))}
              {s.error && <tr><td colSpan={4} className="px-5 py-4 text-ink-500">Stock alerts unavailable.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function KhataMini() {
  const s = useAsync(() => getKhataOverdue(45), []);
  const rows = s.data ? s.data.customers.slice(0, 3) : [];
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-bold">Pending khata <span className="hi">बाकी उधारी</span></h2>
      </div>
      <div className="card divide-y divide-ink-200">
        {s.loading && !s.data ? <div className="h-32 animate-pulse" /> : rows.map((c) => (
          <div key={c.id} className="flex items-center gap-3 p-4">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">{c.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}</span>
            <div className="min-w-0 flex-1">
              <div className="truncate font-semibold">{c.name}</div>
              <div className="text-xs text-ink-500">{c.days_since_payment} days since payment</div>
            </div>
            <div className="text-right font-bold tabular-nums text-red-600">{inr(c.balance)}</div>
          </div>
        ))}
        <button className="w-full p-4 text-center text-sm font-bold text-brand-600" onClick={() => go("khata")}>Open full khata register</button>
      </div>
    </section>
  );
}

function Section({ title, hi, right, children }) {
  return (
    <section className="card p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold">{title} {hi && <span className="hi">{hi}</span>}</h2>
        {right}
      </div>
      {children}
    </section>
  );
}
