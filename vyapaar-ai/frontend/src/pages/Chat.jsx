import { useEffect, useRef, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { sendChat } from "../api/index.js";
import { DataTable } from "../components/ui.jsx";
import Icon from "../components/Icon.jsx";
import { useLang } from "../i18n/index.jsx";

const SUGGESTIONS = [
  { icon: "alert", key: "suggestion_1" },
  { icon: "book", key: "suggestion_2" },
  { icon: "sparkle", key: "suggestion_3" },
  { icon: "box", key: "suggestion_4" },
  { icon: "chart", key: "suggestion_5" },
  { icon: "chat", key: "suggestion_6" },
];

const SR = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

export default function Chat() {
  const { lang, t } = useLang();
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
      const r = await sendChat(message, lang);
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
    r.lang = lang === "hi" ? "hi-IN" : "en-IN";
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
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-100 text-brand-700">
            <Icon name="bot" className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-lg font-extrabold">{t("chat_assistant_title")}</h1>
            <p className="text-sm text-ink-500">{t("chat_assistant_desc")}</p>
          </div>
        </div>
        {msgs.length > 0 && (
          <button
            className="btn-ghost inline-flex items-center gap-1.5 !px-3 !py-1.5 text-xs"
            onClick={() => setMsgs([])}
          >
            <Icon name="trash" className="h-4 w-4" />
            <span>{t("clear_chat")}</span>
          </button>
        )}
      </div>

      <div className="flex-1 space-y-4">
        {msgs.length === 0 && (
          <div className="mx-auto max-w-2xl py-6 text-center">
            <h2 className="text-3xl font-extrabold">{t("chat_welcome_title")}</h2>
            <p className="mt-2 text-ink-500">{t("chat_welcome_desc")}</p>
            <div className="mt-5 grid gap-3 text-left sm:grid-cols-2">
              {SUGGESTIONS.map((s) => {
                const questionText = t(s.key);
                return (
                  <button
                    key={s.key}
                    onClick={() => ask(questionText)}
                    className="card p-4 text-sm font-bold transition hover:ring-brand-500"
                  >
                    <span className="mb-2 block text-brand-600">
                      <Icon name={s.icon} className="h-5 w-5" />
                    </span>
                    "{questionText}"
                  </button>
                );
              })}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <Message key={i} m={m} onAsk={ask} />
        ))}
        {busy && (
          <div className="flex items-center gap-3" role="status" aria-live="polite">
            <BotAvatar />
            <div className="card px-4 py-3 text-sm text-ink-500">
              <span className="animate-pulse">{t("chat_checking_data")}</span>
            </div>
          </div>
        )}
        <div ref={end} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(text);
        }}
        className="sticky bottom-20 mt-4 lg:bottom-4"
      >
        <div className="flex items-center gap-2 rounded-3xl bg-white p-2 shadow-lg ring-1 ring-ink-200">
          <input
            className="min-w-0 flex-1 rounded-2xl bg-transparent px-4 py-3 text-base outline-none"
            placeholder={t("chat_placeholder")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label={t("chat_question_label")}
          />
          <button
            type="submit"
            disabled={busy || !text.trim()}
            className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-600 disabled:opacity-40"
            aria-label={t("chat_send_label")}
          >
            <Icon name="send" className="h-5 w-5" />
          </button>
          {SR && (
            <button
              type="button"
              onClick={mic}
              className={`grid h-11 w-11 place-items-center rounded-2xl text-white ${
                listening ? "animate-pulse bg-red-600" : "bg-brand-600"
              }`}
              aria-label={t("chat_mic_label")}
            >
              <Icon name="mic" className="h-5 w-5" />
            </button>
          )}
        </div>
        <p className="mt-2 text-center text-[11px] font-semibold uppercase tracking-wide text-ink-500">
          {t("chat_footer_note")}
        </p>
      </form>
    </div>
  );
}

const BotAvatar = () => (
  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-brand-100 text-brand-700">
    <Icon name="bot" className="h-5 w-5" />
  </span>
);

function Message({ m, onAsk }) {
  const { t, tName } = useLang();
  if (m.role === "user")
    return (
      <div className="flex items-center justify-end gap-3">
        <div className="max-w-[85%] rounded-3xl rounded-tr-md bg-brand-600 px-5 py-3 font-medium text-white shadow-sm">
          {m.text}
        </div>
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-ink-900 text-white">
          <Icon name="user" className="h-5 w-5" />
        </span>
      </div>
    );
  if (m.role === "error")
    return (
      <div className="flex items-start gap-3">
        <BotAvatar />
        <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200" role="alert">
          {m.text}
        </div>
      </div>
    );

  return (
    <div className="flex items-start gap-3">
      <BotAvatar />
      <div className="card min-w-0 max-w-full p-5 sm:max-w-[85%]">
        <p className="leading-relaxed">{tName(m.answer)}</p>
        {m.blocks?.map((b, i) => (
          <Block key={i} b={b} />
        ))}
        {m.suggestions?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {m.suggestions.map((s) => (
              <button
                key={s}
                onClick={() => onAsk(s)}
                className="rounded-full bg-brand-50 px-3 py-1.5 text-left text-sm font-medium text-brand-700 ring-1 ring-brand-100"
              >
                {tName(s)}
              </button>
            ))}
          </div>
        )}
        <div className="mt-3">
          {m.validated ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-700 ring-1 ring-emerald-200">
              <Icon name="check" className="h-3.5 w-3.5 stroke-[2.5]" />
              <span>{t("verified_against_data")}</span>
            </span>
          ) : (
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-800 ring-1 ring-amber-200">
              {t("rule_based_answer")}
            </span>
          )}
        </div>
        {m.calc?.length > 0 && (
          <details className="mt-3 rounded-2xl bg-ink-100 p-3 text-sm">
            <summary className="cursor-pointer font-semibold">{t("how_calculated")}</summary>
            <ul className="mt-2 space-y-2">
              {m.calc.map((c, i) => (
                <li key={i}>
                  <code className="rounded bg-white px-1.5 py-0.5 text-xs font-bold">{c.tool}</code>{" "}
                  <span className="text-xs text-ink-500">{t("chat_rows", { count: c.row_count })}</span>
                  {c.args && Object.keys(c.args).length > 0 && (
                    <div className="mt-0.5 break-words text-xs text-ink-500">
                      args: {Object.entries(c.args).map(([k, v]) => `${k}=${v}`).join(", ")}
                    </div>
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
  const { tName } = useLang();
  if (b.type === "table")
    return (
      <div className="mt-3">
        <DataTable columns={b.columns} rows={b.rows} compact />
      </div>
    );
  if (b.type === "chart") {
    const chartData = b.data?.map((d) => ({
      ...d,
      [b.x]: tName ? tName(d[b.x]) : d[b.x],
    }));
    return (
      <div className="mt-3 h-44">
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" vertical={false} />
            <XAxis dataKey={b.x} fontSize={11} />
            <YAxis fontSize={11} width={36} />
            <Tooltip />
            <Bar dataKey={b.y} fill="#ea580c" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
  return null;
}
