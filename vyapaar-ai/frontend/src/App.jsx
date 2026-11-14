import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Insights from "./pages/Insights.jsx";
import Restock from "./pages/Restock.jsx";
import Khata from "./pages/Khata.jsx";
import Chat from "./pages/Chat.jsx";
import Upload from "./pages/Upload.jsx";
import { USE_MOCK } from "./api/index.js";
export { go } from "./lib/nav.js";

// Names follow the UX Pilot design. "short" is the label in the phone tab bar.
const TABS = [
  { id: "dashboard", label: "Dashboard", short: "Home", icon: "🏠", el: Dashboard },
  { id: "chat", label: "Ask Vyapaar AI", short: "Ask", icon: "💬", el: Chat },
  { id: "insights", label: "Business Insights", short: "Insights", icon: "📈", el: Insights },
  { id: "restock", label: "Stock Manager", short: "Stock", icon: "📦", el: Restock },
  { id: "khata", label: "Khata Register", short: "Khata", icon: "📒", el: Khata },
  { id: "upload", label: "Data", short: "Data", icon: "🗂️", el: Upload },
];

const fromHash = () => {
  const id = window.location.hash.replace(/^#\/?/, "");
  return TABS.some((t) => t.id === id) ? id : "dashboard";
};

export default function App() {
  const [route, setRoute] = useState(fromHash);
  useEffect(() => {
    const on = () => {
      setRoute(fromHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const Page = TABS.find((t) => t.id === route).el;

  return (
    <div className="min-h-screen lg:pl-64">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-ink-200 bg-white lg:flex">
        <div className="p-5"><Brand /></div>
        <nav className="space-y-1 px-4">
          {TABS.map((t) => (
            <a
              key={t.id}
              href={`#/${t.id}`}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                route === t.id ? "bg-brand-600 text-white shadow-sm" : "text-ink-500 hover:bg-ink-100"
              }`}
            >
              <span className="w-5 text-center">{t.icon}</span>
              {t.label}
            </a>
          ))}
        </nav>
        <div className="mt-auto border-t border-ink-200 p-4">
          {USE_MOCK && <p className="mb-3 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">Demo mode: saved sample data (mock API).</p>}
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-full bg-brand-100 font-bold text-brand-700">RS</span>
            <div className="leading-tight">
              <div className="text-sm font-bold">Rajesh Sharma</div>
              <div className="text-xs text-ink-500">Kirana Store Owner</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-ink-200 bg-white px-4 py-3 lg:hidden">
        <Brand />
        {USE_MOCK && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">mock</span>}
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-28 pt-5 lg:px-8 lg:pb-10 lg:pt-8">
        <Page />
      </main>

      {/* Mobile bottom tab bar (phone-first) */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-6 border-t border-ink-200 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden">
        {TABS.map((t) => (
          <a
            key={t.id}
            href={`#/${t.id}`}
            className={`flex flex-col items-center gap-0.5 py-2 text-[11px] font-semibold ${route === t.id ? "text-brand-600" : "text-ink-500"}`}
          >
            <span className="text-lg leading-none">{t.icon}</span>
            {t.short}
          </a>
        ))}
      </nav>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600 text-lg text-white">🛒</span>
      <div className="leading-tight">
        <div className="text-lg font-bold">Vyapaar AI</div>
      </div>
    </div>
  );
}
