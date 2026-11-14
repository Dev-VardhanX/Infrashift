import React, { createContext, useContext, useState, useEffect } from "react";
import { go } from "../lib/nav.js";

const AuthContext = createContext(null);
const STORAGE_KEY = "vyapaar_auth_user";

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.name === "string" && typeof parsed.shopName === "string") {
      // Strictly ensure only name and shopName exist
      return { name: parsed.name, shopName: parsed.shopName };
    }
  } catch {
    // ignore
  }
  return null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser);

  // Sync if storage changes
  useEffect(() => {
    const onStorage = () => {
      setUser(getStoredUser());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const saveUser = (userData) => {
    // NEVER store password, phone or sensitive info
    const safeUser = {
      name: userData.name || "Rajesh Sharma",
      shopName: userData.shopName || "Sharma General Store",
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(safeUser));
    } catch {
      // ignore
    }
    setUser(safeUser);
    return safeUser;
  };

  const login = async (identifier, password) => {
    // 600ms simulated network delay
    await new Promise((r) => setTimeout(r, 600));

    let derivedName = "Rajesh Sharma";
    let derivedShop = "Sharma General Store";

    if (identifier && identifier.includes("@")) {
      const prefix = identifier.split("@")[0].replace(/[._-]/g, " ");
      derivedName = prefix
        .split(" ")
        .filter(Boolean)
        .map((w) => w[0].toUpperCase() + w.slice(1))
        .join(" ") || "Store Owner";
      derivedShop = `${derivedName}'s Kirana`;
    }

    saveUser({ name: derivedName, shopName: derivedShop });
    go("dashboard");
  };

  const signup = async ({ ownerName, shopName }) => {
    // 600ms simulated network delay
    await new Promise((r) => setTimeout(r, 600));

    saveUser({
      name: ownerName?.trim() || "Rajesh Sharma",
      shopName: shopName?.trim() || "Sharma General Store",
    });
    go("dashboard");
  };

  const loginDemo = async () => {
    saveUser({ name: "Rajesh Sharma", shopName: "Sharma General Store" });
    go("dashboard");
  };

  const logout = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setUser(null);
    go("login");
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, loginDemo, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

