import { useEffect, useRef, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { sendChat } from "../api/index.js";
import { DataTable } from "../components/ui.jsx";

const SUGGESTIONS = [
  { icon: "📉", q: "Which items will run out in the next 3 days?" },
  { icon: "📒", q: "Who owes me money for more than 45 days?" },
  { icon: "🪔", q: "How did Diwali week go compared to the week before?" },
  { icon: "🧱", q: "Which products are dead stock and how much money is stuck?" },
  { icon: "💳", q: "UPI vs cash split in the last 30 days?" },
  { icon: "🗣️", q: "Kitna udhaar baaki hai?" },
];

const SR = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

export default function Chat() {
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const end = useRef(null);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [msgs, busy]);

  async function ask(q) {
    const message = q.trim();
    if (!message || busy) return;
    setText("");
    setMsgs((m) => [...m, { role: "user", text: message }]);
    setBusy(true);
    try {
      const r = await sendChat(message);
      setMsgs((m) => [...m, { role: "bot", ...r }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "error", text: e.message }]);
    } finally {
      setBusy(false);
    }
  }

  function mic() {
    if (!SR) return;
    const r = new SR();
    r.lang = "hi-IN"; // understands Hindi and Hinglish speech
    r.onresult = (e) => setText(e.results[0][0].transcript);
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    setListening(true);
    r.start();
  }

  return (
    <div className="flex min-h-[calc(100vh-11rem)] flex-col lg:min-h-[calc(100vh-5rem)]">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-100 text-xl">🤖</span>
          <div>
            <h1 className="text-lg font-extrabold">Vyapaar AI Assistant</h1>
            <p className="text-sm text-ink-500">Your digital business partner. Ask me anything.</p>
          </div>
        </div>
        {msgs.length > 0 && <button className="btn-ghost !px-3 !py-1.5 text-xs" onClick={() => setMsgs([])}>🗑 Clear chat</button>}
      </div>

      <div className="flex-1 space-y-4">
        {msgs.length === 0 && (
          <div className="mx-auto max-w-2xl py-6 text-center">
            <h2 className="text-3xl font-extrabold">Namaste, Rajesh ji!</h2>
            <p className="mt-2 text-ink-500">I can help you analyse your shop's performance, manage khata or plan stock. Try one of these:</p>
            <div className="mt-5 grid gap-3 text-left sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button key={s.q} onClick={() => ask(s.q)} className="card p-4 text-sm font-bold transition hover:ring-brand-500">
                  <span className="mb-2 block text-lg">{s.icon}</span>"{s.q}"
                </button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => <Message key={i} m={m} onAsk={ask} />)}
        {busy && (
          <div className="flex items-center gap-3" role="status" aria-live="polite">
            <BotAvatar />
            <div className="card px-4 py-3 text-sm text-ink-500"><span className="animate-pulse">Checking your data...</span></div>
          </div>
        )}
        <div ref={end} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); ask(text); }} className="sticky bottom-20 mt-4 lg:bottom-4">
        <div className="flex items-center gap-2 rounded-3xl bg-white p-2 shadow-lg ring-1 ring-ink-200">
          <input
            className="min-w-0 flex-1 rounded-2xl bg-transparent px-4 py-3 text-base outline-none"
            placeholder="Type your business question (e.g. Aaj ki total sale?)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label="Your question"
          />
          <button type="submit" disabled={busy || !text.trim()} className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-600 disabled:opacity-40" aria-label="Send">➤</button>
          {SR && (
            <button type="button" onClick={mic} className={`grid h-11 w-11 place-items-center rounded-2xl text-white ${listening ? "animate-pulse bg-red-600" : "bg-brand-600"}`} aria-label="Speak your question">🎤</button>
          )}
        </div>
        <p className="mt-2 text-center text-[11px] font-semibold uppercase tracking-wide text-ink-500">Supports Hindi &amp; English · Answers come from your data only</p>
      </form>
    </div>
  );
}

const BotAvatar = () => <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand-100 text-lg">🤖</span>;

function Message({ m, onAsk }) {
  if (m.role === "user")
    return (
      <div className="flex items-center justify-end gap-3">
        <div className="max-w-[85%] rounded-3xl rounded-tr-md bg-brand-600 px-5 py-3 font-medium text-white shadow-sm">{m.text}</div>
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-ink-900 text-white">👤</span>
      </div>
    );
  if (m.role === "error")
    return (
      <div className="flex items-start gap-3"><BotAvatar />
        <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200" role="alert">{m.text}</div>
      </div>
    );

  return (
    <div className="flex items-start gap-3">
      <BotAvatar />
      <div className="card min-w-0 max-w-full p-5 sm:max-w-[85%]">
        <p className="leading-relaxed">{m.answer}</p>
        {m.blocks?.map((b, i) => <Block key={i} b={b} />)}
        {m.suggestions?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {m.suggestions.map((s) => (
              <button key={s} onClick={() => onAsk(s)} className="rounded-full bg-brand-50 px-3 py-1.5 text-left text-sm font-medium text-brand-700 ring-1 ring-brand-100">{s}</button>
            ))}
          </div>
        )}
        <div className="mt-3">
          {m.validated ? (
            <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-700 ring-1 ring-emerald-200">✓ Verified against your data</span>
          ) : (
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-800 ring-1 ring-amber-200">Rule-based answer</span>
          )}
        </div>
        {m.calc?.length > 0 && (
          <details className="mt-3 rounded-2xl bg-ink-100 p-3 text-sm">
            <summary className="cursor-pointer font-semibold">How I calculated this</summary>
            <ul className="mt-2 space-y-2">
              {m.calc.map((c, i) => (
                <li key={i}>
                  <code className="rounded bg-white px-1.5 py-0.5 text-xs font-bold">{c.tool}</code>{" "}
                  <span className="text-xs text-ink-500">{c.row_count} rows</span>
                  {c.args && Object.keys(c.args).length > 0 && (
                    <div className="mt-0.5 break-words text-xs text-ink-500">args: {Object.entries(c.args).map(([k, v]) => `${k}=${v}`).join(", ")}</div>
                  )}
                  <div className="mt-0.5 text-ink-700">{c.method}</div>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}

/** blocks[] from POST /chat. table: {type,columns,rows}. chart: {type,kind:"bar",x,y,data}. Unknown types are ignored. */
function Block({ b }) {
  if (b.type === "table") return <div className="mt-3"><DataTable columns={b.columns} rows={b.rows} compact /></div>;
  if (b.type === "chart")
    return (
      <div className="mt-3 h-44">
        <ResponsiveContainer>
          <BarChart data={b.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" vertical={false} />
            <XAxis dataKey={b.x} fontSize={11} />
            <YAxis fontSize={11} width={36} />
            <Tooltip />
            <Bar dataKey={b.y} fill="#ea580c" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  return null;
}
