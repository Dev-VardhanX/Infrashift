import React, { useState } from "react";
import { useAuth } from "../auth/index.jsx";
import { useLang } from "../i18n/index.jsx";
import Icon from "../components/Icon.jsx";
import { LangToggle } from "../App.jsx";

export default function Login() {
  const { login, loginDemo } = useAuth();
  const { t } = useLang();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!identifier.trim() || !password.trim()) {
      setError(t("auth_err_creds"));
      return;
    }

    setLoading(true);
    try {
      await login(identifier, password);
    } catch {
      setError(t("something_went_wrong"));
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    try {
      await loginDemo();
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = (e) => {
    e.preventDefault();
    setToast(t("auth_forgot_password_toast"));
    setTimeout(() => setToast(null), 3500);
  };

  return (
    <div className="relative flex min-h-screen flex-col justify-center bg-brand-50/40 px-4 py-8 sm:px-6 lg:px-8">
      {/* Top right language switcher */}
      <div className="absolute right-4 top-4">
        <LangToggle />
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          role="status"
          className="fixed top-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-2xl bg-ink-900 px-4 py-2.5 text-xs font-semibold text-white shadow-lg"
        >
          <Icon name="sparkle" className="h-4 w-4 text-brand-500" />
          <span>{toast}</span>
        </div>
      )}

      <div className="mx-auto w-full max-w-md">
        {/* Brand logo & title */}
        <div className="text-center">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-md">
            <Icon name="cart" className="h-8 w-8" />
          </div>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-ink-900 sm:text-3xl">
            {t("brand_name")}
          </h1>
          <p className="mt-1 text-sm text-ink-500">{t("auth_tagline")}</p>
        </div>

        {/* Login Card */}
        <div className="card mt-6 p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {error && (
              <div
                className="flex items-center gap-2 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700 ring-1 ring-red-200"
                role="alert"
              >
                <Icon name="alert" className="h-4 w-4 shrink-0 text-red-500" />
                <span>{error}</span>
              </div>
            )}

            {/* Email or Phone field */}
            <div>
              <label htmlFor="login-identifier" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                {t("auth_email_or_phone")}
              </label>
              <input
                id="login-identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                required
                className="mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 ring-ink-200 transition focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder={t("auth_email_or_phone_placeholder")}
                value={identifier}
                onChange={(e) => {
                  setIdentifier(e.target.value);
                  if (error) setError("");
                }}
              />
            </div>

            {/* Password field */}
            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="login-password" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_password")}
                </label>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline"
                >
                  {t("auth_forgot_password")}
                </button>
              </div>
              <div className="relative mt-1.5">
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  className="w-full rounded-xl bg-white px-3.5 py-2.5 pr-10 text-sm ring-1 ring-ink-200 transition focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder={t("auth_password_placeholder")}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError("");
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-ink-500 hover:text-ink-900"
                  aria-label={showPassword ? t("auth_hide_password") : t("auth_show_password")}
                >
                  <Icon name={showPassword ? "eye-off" : "eye"} className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-2 w-full shadow-sm"
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>{t("auth_logging_in")}</span>
                </span>
              ) : (
                t("auth_login_btn")
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-ink-200" />
            <span className="text-[11px] font-bold uppercase tracking-wider text-ink-500">
              OR
            </span>
            <div className="h-px flex-1 bg-ink-200" />
          </div>

          {/* Continue with demo store button */}
          <button
            type="button"
            disabled={loading}
            onClick={handleDemoLogin}
            className="btn-ghost w-full font-semibold hover:border-brand-500 hover:bg-brand-50 hover:text-brand-700"
          >
            <Icon name="sparkle" className="h-4 w-4 text-brand-600" />
            <span>{t("auth_demo_store_btn")}</span>
          </button>

          {/* Demo note */}
          <p className="mt-4 text-center text-xs text-ink-500">
            {t("auth_demo_notice")}
          </p>

          {/* Link to Sign up */}
          <div className="mt-6 border-t border-ink-200 pt-4 text-center text-xs text-ink-500">
            {t("auth_no_account")}{" "}
            <a
              href="#/signup"
              className="font-bold text-brand-600 hover:text-brand-700 hover:underline"
            >
              {t("auth_sign_up_link")}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

