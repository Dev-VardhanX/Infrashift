import { useState } from "react";
import { Modal } from "./ui.jsx";
import { Loading, ErrorState } from "./States.jsx";

/** Shows drafts from POST /actions/draft: one card per supplier / customer with Copy + WhatsApp. */
export default function DraftModal({ title, state, onClose, extra }) {
  return (
    <Modal title={title} onClose={onClose}>
      {extra}
      {state.loading && <Loading label="Drafting..." />}
      {state.error && <ErrorState error={state.error} onRetry={state.reload} />}
      {state.data && (state.data.drafts.length === 0 ? (
        <p className="py-6 text-center text-sm text-ink-500">Nothing to draft.</p>
      ) : (
        <div className="space-y-3">
          {state.data.drafts.map((d, i) => (
            <DraftCard key={i} draft={d} />
          ))}
        </div>
      ))}
    </Modal>
  );
}

function DraftCard({ draft }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(draft.text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = draft.text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }
  return (
    <div className="rounded-xl bg-ink-100 p-3">
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-500">To: {draft.to}</div>
      <pre className="whitespace-pre-wrap break-words font-sans text-sm">{draft.text}</pre>
      <div className="mt-3 flex gap-2">
        <button className="btn-ghost flex-1" onClick={copy}>
          {copied ? "Copied ✓" : "Copy"}
        </button>
        <a className="btn-primary flex-1" href={draft.wa_link} target="_blank" rel="noopener noreferrer">
          WhatsApp
        </a>
      </div>
    </div>
  );
}
