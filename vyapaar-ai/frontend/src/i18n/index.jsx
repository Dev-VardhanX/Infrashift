import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import en from "./en.js";
import hi from "./hi.js";
import { tEntity } from "./entities.js";

const LangContext = createContext(null);
const STORAGE_KEY = "vyapaar_lang";

function getInitialLang() {
  try {
    const search = new URLSearchParams(window.location.search);
    const qLang = search.get("lang");
    if (qLang === "hi" || qLang === "en") return qLang;
  } catch {
    // ignore
  }
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "hi" || saved === "en") return saved;
  } catch {
    // localStorage might be unavailable
  }
  return "en";
}

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(getInitialLang);

  const setLang = (next) => {
    const val = typeof next === "function" ? next(lang) : next;
    if (val === "hi" || val === "en") {
      setLangState(val);
      try {
        localStorage.setItem(STORAGE_KEY, val);
      } catch {
        // ignore
      }
    }
  };

  useEffect(() => {
    try {
      document.documentElement.lang = lang;
    } catch {
      // ignore
    }
  }, [lang]);

  const value = useMemo(() => {
    const dict = lang === "hi" ? hi : en;
    const t = (key, params) => {
      let str = dict[key] ?? en[key] ?? key;
      if (params && typeof str === "string") {
        str = str.replace(/\{(\w+)\}/g, (match, paramName) => {
          return params[paramName] !== undefined ? params[paramName] : match;
        });
      }
      return str;
    };
    const tName = (val) => tEntity(val, lang);
    return { lang, setLang, t, tName };
  }, [lang]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) {
    throw new Error("useLang must be used within a LangProvider");
  }
  return ctx;
}
