import { useState } from "react";
import { getInsights, draftAction } from "../api/index.js";
import { useAsync } from "../lib/useAsync.js";
import { Async, EmptyState } from "../components/States.jsx";
import { PageHeader, SeverityBadge, DataTable } from "../components/ui.jsx";
import DraftModal from "../components/DraftModal.jsx";
import Icon from "../components/Icon.jsx";
import { inr } from "../lib/format.js";
import { go } from "../lib/nav.js";
import { useLang } from "../i18n/index.jsx";

const ICON = {
  margin_leak: "chart",
  expense_anomaly: "alert",
  dead_stock: "box",
  restock: "cart",
  khata_overdue: "book",
  festive_lift: "sparkle",
};

export default function Insights() {
  const { t } = useLang();
  const state = useAsync(getInsights, []);
  const [open, setOpen] = useState(null); // draft modal state
  const draft = useAsync(() => (open ? draftAction("purchase_order", open.skus) : Promise.resolve(null)), [open]);

  // Backend already sorts by impact, but sort again so the UI never depends on it.
  const sev = { high: 0, medium: 1, low: 2 };

  return (
    <>
      <PageHeader title={t("insights_title")} subtitle={t("insights_subtitle")} />
      <Async
        state={state}
        isEmpty={(d) => !d.insights?.length}
        empty={<EmptyState icon="check" title={t("empty_insights_title")} hint={t("empty_insights_hint")} />}
      >
        {(d) => (
          <div className="grid gap-4 lg:grid-cols-2">
            {[...d.insights]
              .sort((a, b) => b.impact_inr - a.impact_inr || sev[a.severity] - sev[b.severity])
              .map((i) => (
                <Card key={i.id} i={i} onDraftPo={(skus) => setOpen({ skus })} />
              ))}
          </div>
        )}
      </Async>
      {open && <DraftModal title={t("purchase_order_drafts")} state={draft} onClose={() => setOpen(null)} />}
    </>
  );
}

function Card({ i, onDraftPo }) {
  const { t, tName } = useLang();
  const [showWhy, setShowWhy] = useState(false);
  const k = i.action?.kind;

  return (
    <article className="card p-5">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600" aria-hidden>
          <Icon name={ICON[i.type] ?? "sparkle"} className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={i.severity} />
            {i.impact_inr > 0 && (
              <span className="text-xs font-semibold text-ink-700">
                {t("impact_amount", { amount: inr(i.impact_inr) })}
              </span>
            )}
          </div>
          <h3 className="mt-1 font-semibold leading-snug">{tName(i.title)}</h3>
        </div>
      </div>

      {i.evidence?.rows?.length > 0 && (
        <div className="mt-3">
          <DataTable columns={i.evidence.columns} rows={i.evidence.rows} compact />
        </div>
      )}

      <button
        className="mt-3 text-sm font-medium text-brand-700"
        onClick={() => setShowWhy((v) => !v)}
        aria-expanded={showWhy}
      >
        {showWhy ? t("hide") : t("why_seeing_this")}
      </button>
      {showWhy && <p className="mt-1 rounded-lg bg-ink-100 p-3 text-sm text-ink-700">{tName(i.why)}</p>}

      {i.action && (
        <div className="mt-3">
          {k === "draft_po" && (
            <button className="btn-primary" onClick={() => onDraftPo(i.action.payload?.skus ?? [])}>
              {t("draft_po")}
            </button>
          )}
          {k === "whatsapp_reminder" && (
            <button className="btn-primary" onClick={() => go("khata")}>
              {t("send_reminder")}
            </button>
          )}
          {(!k || k === "none") && i.action.label && (
            <span className="inline-block rounded-lg bg-brand-50 px-3 py-1.5 text-sm text-brand-700">
              {t("suggested_action", { action: tName(i.action.label) })}
            </span>
          )}
        </div>
      )}
    </article>
  );
}
