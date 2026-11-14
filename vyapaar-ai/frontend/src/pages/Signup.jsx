import React, { useState } from "react";
import { useAuth } from "../auth/index.jsx";
import { useLang } from "../i18n/index.jsx";
import Icon from "../components/Icon.jsx";
import { LangToggle } from "../App.jsx";

export default function Signup() {
  const { signup } = useAuth();
  const { t } = useLang();

  const [formData, setFormData] = useState({
    ownerName: "",
    shopName: "",
    shopType: "",
    phone: "",
    email: "",
    password: "",
    confirmPassword: "",
    terms: false,
  });

  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validate = () => {
    const errs = {};

    if (!formData.ownerName.trim()) {
      errs.ownerName = t("auth_err_owner_name");
    }

    if (!formData.shopName.trim()) {
      errs.shopName = t("auth_err_shop_name");
    }

    if (!formData.shopType) {
      errs.shopType = t("auth_err_shop_type");
    }

    // 10-digit Indian phone validation: starts with 6-9, exactly 10 digits
    const cleanPhone = formData.phone.trim().replace(/^(\+91|0)/, "").replace(/[\s-]/g, "");
    if (!/^[6-9]\d{9}$/.test(cleanPhone)) {
      errs.phone = t("auth_err_phone");
    }

    // Email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errs.email = t("auth_err_email");
    }

    // Password >= 8 characters
    if (formData.password.length < 8) {
      errs.password = t("auth_err_password_len");
    }

    // Passwords match
    if (formData.password !== formData.confirmPassword) {
      errs.confirmPassword = t("auth_err_password_match");
    }

    // Terms accepted
    if (!formData.terms) {
      errs.terms = t("auth_err_terms");
    }

    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      await signup({
        ownerName: formData.ownerName,
        shopName: formData.shopName,
      });
    } catch {
      setErrors({ form: t("something_went_wrong") });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col justify-center bg-brand-50/40 px-4 py-8 sm:px-6 lg:px-8">
      {/* Top right language switcher */}
      <div className="absolute right-4 top-4">
        <LangToggle />
      </div>

      <div className="mx-auto w-full max-w-lg">
        {/* Brand logo & header */}
        <div className="text-center">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-md">
            <Icon name="cart" className="h-8 w-8" />
          </div>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-ink-900 sm:text-3xl">
            {t("auth_signup_title")}
          </h1>
          <p className="mt-1 text-sm text-ink-500">{t("auth_signup_subtitle")}</p>
        </div>

        {/* Signup Card */}
        <div className="card mt-6 p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {errors.form && (
              <div
                className="flex items-center gap-2 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700 ring-1 ring-red-200"
                role="alert"
              >
                <Icon name="alert" className="h-4 w-4 shrink-0 text-red-500" />
                <span>{errors.form}</span>
              </div>
            )}

            {/* Owner Name & Shop Name (2 cols on sm) */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="signup-owner" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_owner_name")} *
                </label>
                <input
                  id="signup-owner"
                  name="ownerName"
                  type="text"
                  required
                  className={`mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                    errors.ownerName ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                  }`}
                  placeholder={t("auth_owner_name_placeholder")}
                  value={formData.ownerName}
                  onChange={handleChange}
                />
                {errors.ownerName && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.ownerName}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-shop" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_shop_name")} *
                </label>
                <input
                  id="signup-shop"
                  name="shopName"
                  type="text"
                  required
                  className={`mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                    errors.shopName ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                  }`}
                  placeholder={t("auth_shop_name_placeholder")}
                  value={formData.shopName}
                  onChange={handleChange}
                />
                {errors.shopName && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.shopName}</p>
                )}
              </div>
            </div>

            {/* Shop Type Dropdown */}
            <div>
              <label htmlFor="signup-type" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                {t("auth_shop_type")} *
              </label>
              <select
                id="signup-type"
                name="shopType"
                required
                className={`mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                  errors.shopType ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                }`}
                value={formData.shopType}
                onChange={handleChange}
              >
                <option value="">{t("auth_select_shop_type")}</option>
                <option value="kirana">{t("auth_type_kirana")}</option>
                <option value="general">{t("auth_type_general")}</option>
                <option value="pharmacy">{t("auth_type_pharmacy")}</option>
                <option value="other">{t("auth_type_other")}</option>
              </select>
              {errors.shopType && (
                <p className="mt-1 text-xs text-red-600 font-medium">{errors.shopType}</p>
              )}
            </div>

            {/* Phone & Email (2 cols on sm) */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="signup-phone" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_phone")} *
                </label>
                <input
                  id="signup-phone"
                  name="phone"
                  type="tel"
                  required
                  className={`mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                    errors.phone ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                  }`}
                  placeholder={t("auth_phone_placeholder")}
                  value={formData.phone}
                  onChange={handleChange}
                />
                {errors.phone && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.phone}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-email" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_email")} *
                </label>
                <input
                  id="signup-email"
                  name="email"
                  type="email"
                  required
                  className={`mt-1.5 w-full rounded-xl bg-white px-3.5 py-2.5 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                    errors.email ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                  }`}
                  placeholder={t("auth_email_placeholder")}
                  value={formData.email}
                  onChange={handleChange}
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.email}</p>
                )}
              </div>
            </div>

            {/* Password & Confirm Password (2 cols on sm) */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="signup-password" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_password")} *
                </label>
                <div className="relative mt-1.5">
                  <input
                    id="signup-password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className={`w-full rounded-xl bg-white px-3.5 py-2.5 pr-10 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                      errors.password ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                    }`}
                    placeholder={t("auth_password_placeholder")}
                    value={formData.password}
                    onChange={handleChange}
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
                {errors.password && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="signup-confirm-password" className="block text-xs font-bold uppercase tracking-wider text-ink-700">
                  {t("auth_confirm_password")} *
                </label>
                <div className="relative mt-1.5">
                  <input
                    id="signup-confirm-password"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className={`w-full rounded-xl bg-white px-3.5 py-2.5 pr-10 text-sm ring-1 transition focus:outline-none focus:ring-2 ${
                      errors.confirmPassword ? "ring-red-400 focus:ring-red-500" : "ring-ink-200 focus:ring-brand-500"
                    }`}
                    placeholder={t("auth_confirm_password_placeholder")}
                    value={formData.confirmPassword}
                    onChange={handleChange}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-ink-500 hover:text-ink-900"
                    aria-label={showConfirmPassword ? t("auth_hide_password") : t("auth_show_password")}
                  >
                    <Icon name={showConfirmPassword ? "eye-off" : "eye"} className="h-4 w-4" />
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* Terms checkbox */}
            <div className="pt-1">
              <label className="flex items-start gap-2.5 text-xs text-ink-700 cursor-pointer">
                <input
                  type="checkbox"
                  name="terms"
                  checked={formData.terms}
                  onChange={handleChange}
                  className="mt-0.5 h-4 w-4 rounded accent-orange-600"
                />
                <span>{t("auth_terms")}</span>
              </label>
              {errors.terms && (
                <p className="mt-1 text-xs text-red-600 font-medium">{errors.terms}</p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-3 w-full shadow-sm"
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>{t("auth_signing_up")}</span>
                </span>
              ) : (
                t("auth_signup_btn")
              )}
            </button>
          </form>

          {/* Demo note */}
          <p className="mt-4 text-center text-xs text-ink-500">
            {t("auth_demo_notice")}
          </p>

          {/* Link back to Login */}
          <div className="mt-6 border-t border-ink-200 pt-4 text-center text-xs text-ink-500">
            {t("auth_already_have_account")}{" "}
            <a
              href="#/login"
              className="font-bold text-brand-600 hover:text-brand-700 hover:underline"
            >
              {t("auth_log_in_link")}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

