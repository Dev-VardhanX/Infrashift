import { useState } from "react";
import { getInsights, draftAction } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { Async, EmptyState } from "../components/States.jsx";
import { PageHeader, SeverityBadge, DataTable } from "../components/ui.jsx";
import DraftModal from "../components/DraftModal.jsx";
import { inr } from "../lib/format.js";
import { go } from "../lib/nav.js";

const ICON = { margin_leak: "📉", expense_anomaly: "🧾", dead_stock: "🧱", restock: "📦", khata_overdue: "📒", festive_lift: "🪔" };

export default function Insights() {
  const state = useAsync(getInsights, []);
  const [open, setOpen] = useState(null); // draft modal state
  const draft = useAsync(() => (open ? draftAction("purchase_order", open.skus) : Promise.resolve(null)), [open]);

  // Backend already sorts by impact, but sort again so the UI never depends on it.
  const sev = { high: 0, medium: 1, low: 2 };

  return (
    <>
      <PageHeader title="Business Insights" subtitle="व्यापार का विश्लेषण · what needs your attention, biggest rupee impact first" />
      <Async state={state} isEmpty={(d) => !d.insights?.length}
        empty={<EmptyState icon="✅" title="Nothing needs attention" hint="No rules fired on your data." />}>
        {(d) => (
          <div className="grid gap-4 lg:grid-cols-2">
            {[...d.insights].sort((a, b) => b.impact_inr - a.impact_inr || sev[a.severity] - sev[b.severity]).map((i) => (
              <Card key={i.id} i={i} onDraftPo={(skus) => setOpen({ skus })} />
            ))}
          </div>
        )}
      </Async>
      {open && (
        <DraftModal title="Purchase order draft" state={draft} onClose={() => setOpen(null)} />
      )}
    </>
  );
}

function Card({ i, onDraftPo }) {
  const [showWhy, setShowWhy] = useState(false);
  const k = i.action?.kind;
  return (
    <article className="card p-5">
      <div className="flex items-start gap-3">
        <span className="text-2xl" aria-hidden>{ICON[i.type] ?? "💡"}</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={i.severity} />
            {i.impact_inr > 0 && <span className="text-xs font-semibold text-ink-700">Impact {inr(i.impact_inr)}</span>}
          </div>
          <h3 className="mt-1 font-semibold leading-snug">{i.title}</h3>
        </div>
      </div>

      {i.evidence?.rows?.length > 0 && (
        <div className="mt-3"><DataTable columns={i.evidence.columns} rows={i.evidence.rows} compact /></div>
      )}

      <button className="mt-3 text-sm font-medium text-brand-700" onClick={() => setShowWhy((v) => !v)} aria-expanded={showWhy}>
        {showWhy ? "Hide" : "Why am I seeing this?"}
      </button>
      {showWhy && <p className="mt-1 rounded-lg bg-ink-100 p-3 text-sm text-ink-700">{i.why}</p>}

      {i.action && (
        <div className="mt-3">
          {k === "draft_po" && <button className="btn-primary" onClick={() => onDraftPo(i.action.payload?.skus ?? [])}>{i.action.label}</button>}
          {k === "whatsapp_reminder" && <button className="btn-primary" onClick={() => go("khata")}>{i.action.label}</button>}
          {(!k || k === "none") && i.action.label && (
            <span className="inline-block rounded-lg bg-brand-50 px-3 py-1.5 text-sm text-brand-700">Suggested: {i.action.label}</span>
          )}
        </div>
      )}
    </article>
  );
}
