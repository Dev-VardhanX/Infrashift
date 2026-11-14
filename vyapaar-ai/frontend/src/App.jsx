import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Insights from "./pages/Insights.jsx";
import Restock from "./pages/Restock.jsx";
import Khata from "./pages/Khata.jsx";
import Chat from "./pages/Chat.jsx";
import Upload from "./pages/Upload.jsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import { USE_MOCK } from "./api/index.js";
import { useLang } from "./i18n/index.jsx";
import { useAuth } from "./auth/index.jsx";
import Icon from "./components/Icon.jsx";
export { go } from "./lib/nav.js";

// Names follow the UX Pilot design. "shortKey" is the label key in the phone tab bar.
const TABS = [
  { id: "dashboard", labelKey: "nav_dashboard", shortKey: "nav_short_dashboard", icon: "home", el: Dashboard },
  { id: "chat", labelKey: "nav_chat", shortKey: "nav_short_chat", icon: "chat", el: Chat },
  { id: "insights", labelKey: "nav_insights", shortKey: "nav_short_insights", icon: "chart", el: Insights },
  { id: "restock", labelKey: "nav_restock", shortKey: "nav_short_restock", icon: "box", el: Restock },
  { id: "khata", labelKey: "nav_khata", shortKey: "nav_short_khata", icon: "book", el: Khata },
  { id: "upload", labelKey: "nav_upload", shortKey: "nav_short_upload", icon: "data", el: Upload },
];

const fromHash = () => {
  const id = window.location.hash.replace(/^#\/?/, "");
  if (id === "login" || id === "signup") return id;
  return TABS.some((t) => t.id === id) ? id : "dashboard";
};

const userInitials = (name) => {
  if (!name) return "RS";
  return name
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
};

export default function App() {
  const [route, setRoute] = useState(fromHash);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const { t, tName } = useLang();
  const { user, logout } = useAuth();

  useEffect(() => {
    const on = () => {
      setRoute(fromHash());
      setShowMobileMenu(false);
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  // Route guard:
  // - unauthenticated users are redirected to #/login
  // - logged-in users visiting #/login or #/signup are redirected to #/dashboard
  useEffect(() => {
    if (!user && route !== "login" && route !== "signup") {
      window.location.hash = "#/login";
    } else if (user && (route === "login" || route === "signup")) {
      window.location.hash = "#/dashboard";
    }
  }, [user, route]);

  // If not logged in, show login or signup page without shell
  if (!user) {
    if (route === "signup") return <Signup />;
    return <Login />;
  }

  // If logged in and on login/signup, let redirect effect run and render Dashboard
  if (route === "login" || route === "signup") {
    return <Dashboard />;
  }

  const Page = TABS.find((t) => t.id === route)?.el ?? Dashboard;

  return (
    <div className="min-h-screen lg:pl-64">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-ink-200 bg-white lg:flex">
        <div className="p-5"><Brand /></div>
        <nav className="space-y-1 px-4">
          {TABS.map((tItem) => (
            <a
              key={tItem.id}
              href={`#/${tItem.id}`}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                route === tItem.id ? "bg-brand-600 text-white shadow-sm" : "text-ink-500 hover:bg-ink-100"
              }`}
            >
              <Icon name={tItem.icon} className="h-5 w-5 shrink-0" />
              <span>{t(tItem.labelKey)}</span>
            </a>
          ))}
        </nav>
        <div className="mt-auto border-t border-ink-200 p-4">
          {USE_MOCK && (
            <p className="mb-3 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">
              {t("demo_mode_notice")}
            </p>
          )}
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-500">{t("language_label")}</span>
            <LangToggle />
          </div>
          <div className="flex items-center justify-between gap-2 rounded-2xl bg-ink-100 p-2.5">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-100 font-bold text-xs text-brand-700">
                {userInitials(user?.name)}
              </span>
              <div className="min-w-0 flex-1 leading-tight">
                <div className="truncate text-xs font-bold">{tName(user?.name || "Rajesh Sharma")}</div>
                <div className="truncate text-[11px] text-ink-500">{tName(user?.shopName || "Sharma General Store")}</div>
              </div>
            </div>
            <button
              onClick={logout}
              className="rounded-lg p-1.5 text-ink-500 hover:bg-white hover:text-red-600 transition"
              title={t("auth_logout")}
              aria-label={t("auth_logout")}
            >
              <Icon name="logout" className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-ink-200 bg-white px-4 py-3 lg:hidden">
        <Brand />
        <div className="flex items-center gap-2">
          {USE_MOCK && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
              {t("demo_mode_badge")}
            </span>
          )}
          <LangToggle />
          <div className="relative">
            <button
              onClick={() => setShowMobileMenu((v) => !v)}
              className="flex items-center gap-1.5 rounded-xl bg-ink-100 px-2.5 py-1 text-xs font-semibold text-ink-700 hover:bg-ink-200"
              aria-label="User menu"
              aria-expanded={showMobileMenu}
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                {userInitials(user?.name)}
              </span>
              <span className="max-w-[70px] truncate">{tName(user?.shopName || "Sharma General Store")}</span>
            </button>
            {showMobileMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowMobileMenu(false)}
                />
                <div className="absolute right-0 mt-2 w-48 rounded-2xl bg-white p-2 shadow-lg ring-1 ring-ink-200 z-50">
                  <div className="border-b border-ink-100 px-2.5 py-2">
                    <div className="text-xs font-bold truncate">{tName(user?.name || "Rajesh Sharma")}</div>
                    <div className="text-[11px] text-ink-500 truncate">{tName(user?.shopName || "Sharma General Store")}</div>
                  </div>
                  <button
                    onClick={() => {
                      setShowMobileMenu(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-xs font-semibold text-red-600 hover:bg-red-50"
                  >
                    <Icon name="logout" className="h-4 w-4" />
                    <span>{t("auth_logout")}</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-28 pt-5 lg:px-8 lg:pb-10 lg:pt-8">
        <Page />
      </main>

      {/* Mobile bottom tab bar (phone-first) */}
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-6 border-t border-ink-200 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden">
        {TABS.map((tItem) => (
          <a
            key={tItem.id}
            href={`#/${tItem.id}`}
            className={`flex flex-col items-center justify-center gap-1 py-2 text-[11px] font-semibold text-center ${
              route === tItem.id ? "text-brand-600" : "text-ink-500"
            }`}
          >
            <Icon name={tItem.icon} className="h-5 w-5" />
            <span className="truncate px-0.5 max-w-full">{t(tItem.shortKey)}</span>
          </a>
        ))}
      </nav>
    </div>
  );
}

export function LangToggle() {
  const { lang, setLang } = useLang();
  return (
    <div className="inline-flex rounded-lg bg-ink-100 p-0.5 text-xs font-semibold" role="group" aria-label="Language switcher">
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`rounded-md px-2.5 py-1 text-xs transition ${
          lang === "en" ? "bg-white text-brand-600 shadow-sm font-bold" : "text-ink-500 hover:text-ink-900"
        }`}
        aria-pressed={lang === "en"}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLang("hi")}
        className={`rounded-md px-2.5 py-1 text-xs transition ${
          lang === "hi" ? "bg-white text-brand-600 shadow-sm font-bold" : "text-ink-500 hover:text-ink-900"
        }`}
        aria-pressed={lang === "hi"}
      >
        हिं
      </button>
    </div>
  );
}

function Brand() {
  const { t } = useLang();
  return (
    <div className="flex items-center gap-3">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600 text-white">
        <Icon name="cart" className="h-5 w-5" />
      </span>
      <div className="leading-tight">
        <div className="text-lg font-bold">{t("brand_name")}</div>
      </div>
    </div>
  );
}
