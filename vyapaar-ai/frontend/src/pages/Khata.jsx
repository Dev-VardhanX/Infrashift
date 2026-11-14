import { useEffect, useState } from "react";
import { getKhataOverdue, draftAction } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { Async, EmptyState, Loading, ErrorState } from "../components/States.jsx";
import { inr, dmon } from "../lib/format.js";

const initials = (n) => n.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

/** Master-detail like the design: overdue list on the left, selected customer + reminder on the right (stacked on phones). */
export default function Khata() {
  const [days, setDays] = useState(45);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const state = useAsync(() => getKhataOverdue(days), [days]);

  useEffect(() => {
    if (state.data && !state.data.customers.some((c) => c.id === sel)) setSel(window.innerWidth >= 1024 ? state.data.customers[0]?.id ?? null : null);
  }, [state.data]); // eslint-disable-line

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold sm:text-3xl">Khata Register <span className="hi">उधार खाता</span></h1>
          <p className="text-sm text-ink-500">Customers who have not paid for a while</p>
        </div>
        <label className="flex items-center gap-2 text-sm font-medium">
          Overdue after
          <select className="rounded-lg bg-white px-2 py-1.5 ring-1 ring-ink-200" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            {[30, 45, 60, 90].map((d) => <option key={d} value={d}>{d} days</option>)}
          </select>
        </label>
      </div>

      <Async state={state} isEmpty={(d) => !d.customers?.length}
        empty={<EmptyState icon="🎉" title="No overdue khata" hint={`Nobody has gone more than ${days} days without paying.`} />}>
        {(d) => {
          const list = d.customers.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
          const total = d.customers.reduce((s, c) => s + c.balance, 0);
          const cur = d.customers.find((c) => c.id === sel);
          return (
            <div className="grid gap-4 lg:grid-cols-[22rem_1fr]">
              <div className={`card overflow-hidden ${cur ? "hidden lg:block" : ""}`}>
                <div className="space-y-3 p-4">
                  <div className="rounded-2xl bg-red-50 p-3 ring-1 ring-red-100">
                    <div className="text-xs font-bold uppercase tracking-wide text-ink-500">Overdue {days}+ days</div>
                    <div className="text-2xl font-extrabold tabular-nums text-red-600">{inr(total)}</div>
                    <div className="text-xs text-ink-500">{d.customers.length} customers</div>
                  </div>
                  <input className="w-full rounded-xl bg-ink-100 px-3 py-2.5 text-sm outline-none" placeholder="Search customer..." value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search customer" />
                </div>
                <ul className="divide-y divide-ink-200 border-t border-ink-200">
                  {list.map((c) => (
                    <li key={c.id}>
                      <button onClick={() => setSel(c.id)} className={`flex w-full items-center gap-3 border-l-4 p-4 text-left ${sel === c.id ? "border-brand-600 bg-brand-50" : "border-transparent hover:bg-ink-100"}`}>
                        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">{initials(c.name)}</span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate font-bold">{c.name}</span>
                          <span className="text-xs text-ink-500">{c.days_since_payment} days since payment</span>
                        </span>
                        <span className="text-right"><span className="block font-bold tabular-nums text-red-600">{inr(c.balance)}</span><span className="text-[10px] font-bold uppercase text-ink-500">Pending</span></span>
                      </button>
                    </li>
                  ))}
                  {list.length === 0 && <li className="p-4 text-sm text-ink-500">No customer matches "{q}".</li>}
                </ul>
              </div>

              <div className={cur ? "" : "hidden lg:block"}>
                {cur ? <Detail c={cur} onBack={() => setSel(null)} /> : <div className="card p-8 text-center text-ink-500">Select a customer to see details.</div>}
              </div>
            </div>
          );
        }}
      </Async>
    </>
  );
}

function Detail({ c, onBack }) {
  const [lang, setLang] = useState("hi");
  const [copied, setCopied] = useState(false);
  const draft = useAsync(() => draftAction("khata_reminder", [c.id], lang), [c.id, lang]);
  const d0 = draft.data?.drafts?.[0];

  async function copy() {
    try { await navigator.clipboard.writeText(d0.text); } catch { /* clipboard blocked: user can still select the text */ }
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap items-center gap-3 p-5">
        <button className="btn-ghost !px-3 !py-1.5 lg:hidden" onClick={onBack} aria-label="Back to list">←</button>
        <span className="grid h-14 w-14 place-items-center rounded-full bg-brand-100 text-lg font-bold text-brand-700">{initials(c.name)}</span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-xl font-extrabold">{c.name}</h2>
          <p className="text-sm text-ink-500">Last payment {c.last_payment_date ? dmon(c.last_payment_date) : `${c.days_since_payment} days ago`}</p>
        </div>
        {d0 && <a className="btn bg-emerald-600 text-white hover:bg-emerald-700" href={d0.wa_link} target="_blank" rel="noopener noreferrer">🔔 Send reminder</a>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="card p-5"><div className="text-xs font-bold uppercase tracking-wide text-ink-500">Current balance</div><div className="mt-1 text-2xl font-extrabold tabular-nums text-red-600">{inr(c.balance)}</div></div>
        <div className="card p-5"><div className="text-xs font-bold uppercase tracking-wide text-ink-500">Days since payment</div><div className="mt-1 text-2xl font-extrabold tabular-nums">{c.days_since_payment}</div></div>
      </div>
      {c.over_limit && <div className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700 ring-1 ring-red-200">Over credit limit. Do not give fresh khata until this is paid.</div>}

      <div className="card p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-bold">WhatsApp reminder</h3>
          <div className="flex rounded-xl bg-ink-100 p-1 text-sm font-semibold" role="group" aria-label="Language">
            {[["hi", "हिंदी / Hinglish"], ["en", "English"]].map(([v, l]) => (
              <button key={v} onClick={() => setLang(v)} className={`rounded-lg px-3 py-1 ${lang === v ? "bg-white shadow-sm" : "text-ink-500"}`}>{l}</button>
            ))}
          </div>
        </div>
        {draft.loading && !d0 && <Loading label="Drafting..." />}
        {draft.error && <ErrorState error={draft.error} onRetry={draft.reload} />}
        {d0 && (
          <>
            <pre className="whitespace-pre-wrap break-words rounded-2xl bg-ink-100 p-4 font-sans text-sm">{d0.text}</pre>
            <div className="mt-3 flex gap-2">
              <button className="btn-ghost flex-1" onClick={copy}>{copied ? "Copied ✓" : "Copy"}</button>
              <a className="btn flex-1 bg-emerald-600 text-white hover:bg-emerald-700" href={d0.wa_link} target="_blank" rel="noopener noreferrer">Open WhatsApp</a>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
