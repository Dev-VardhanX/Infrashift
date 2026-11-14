// The ONLY module that talks to the backend. Shapes follow docs/02_SYSTEM_DESIGN.md section 3.
// VITE_USE_MOCK=true reads src/api/mock/*.json; false calls the FastAPI server.
import dashboardMock from "./mock/dashboard.json";
import alertsMock from "./mock/alerts.json";
import insightsMock from "./mock/insights.json";
import khataMock from "./mock/khata.json";
import chatMock from "./mock/chat.json";
import loadMock from "./mock/load_sample.json";
import uploadMock from "./mock/upload.json";
import { buildDrafts } from "./mockDrafts.js";

export const USE_MOCK = String(import.meta.env.VITE_USE_MOCK ?? "true") === "true";
const BASE = import.meta.env.VITE_API_BASE || "/api";
const delay = (v, ms = 350) => new Promise((r) => setTimeout(() => r(structuredClone(v)), ms));

export class ApiError extends Error {
  constructor(message, code = "unknown") {
    super(message);
    this.code = code;
  }
}

async function http(path, { method = "GET", body, form } = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: form ?? (body ? JSON.stringify(body) : undefined),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", "network");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const e = data?.error;
    throw new ApiError(e?.message || `Server error (${res.status})`, e?.code || "http_error");
  }
  return data;
}

const qs = (o) => {
  const p = new URLSearchParams();
  Object.entries(o).forEach(([k, v]) => v !== undefined && v !== null && v !== "" && p.set(k, v));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const loadSample = () => (USE_MOCK ? delay(loadMock, 900) : http("/load-sample", { method: "POST" }));

export function uploadFiles(files) {
  if (USE_MOCK) {
    const names = [...files].map((f) => f.name);
    const rep = structuredClone(uploadMock);
    rep.files = names.map((name, i) => rep.files[i] ?? { name, rows_ok: 0, rows_rejected: 0, reasons: {}, mapping: {} });
    return delay(rep, 900);
  }
  const form = new FormData();
  [...files].forEach((f) => form.append("files", f, f.name));
  return http("/upload", { method: "POST", form });
}

export const getDashboard = ({ from, to } = {}) =>
  USE_MOCK ? delay(dashboardMock) : http(`/dashboard${qs({ from, to })}`);

export const getAlerts = () => (USE_MOCK ? delay(alertsMock) : http("/inventory/alerts"));
export const getInsights = () => (USE_MOCK ? delay(insightsMock) : http("/insights"));
export const getKhataOverdue = (days = 45) =>
  USE_MOCK ? delay(khataMock) : http(`/khata/overdue${qs({ days })}`);

export function sendChat(message, lang) {
  if (!USE_MOCK) return http("/chat", { method: "POST", body: { message, lang } });
  const m = message.toLowerCase();
  const hit = chatMock.replies.find((r) => r.keys.some((k) => m.includes(k)));
  return delay(hit ?? chatMock.fallback, 700);
}

/** type: "purchase_order" | "khata_reminder". ids: SKUs for PO, customer ids for reminders. lang: "hi" | "en" */
export function draftAction(type, ids, lang = "hi") {
  if (USE_MOCK) return delay({ drafts: buildDrafts(type, ids, lang, { alertsMock, khataMock }) }, 300);
  return http("/actions/draft", { method: "POST", body: { type, ids, lang } });
}
