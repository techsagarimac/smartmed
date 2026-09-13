import { createContext, useContext, useMemo, useState } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

function readUser() {
  try {
    const raw = localStorage.getItem("smartmed_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser);
  const [token, setToken] = useState(localStorage.getItem("smartmed_token"));

  const remember = (payload) => {
    localStorage.setItem("smartmed_token", payload.access_token);
    localStorage.setItem("smartmed_user", JSON.stringify(payload.user));
    setToken(payload.access_token);
    setUser(payload.user);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token),
      async login(email, password) {
        const payload = await api.login({ email, password });
        remember(payload);
        return payload.user;
      },
      async register(name, email, password) {
        const payload = await api.register({ name, email, password });
        remember(payload);
        return payload.user;
      },
      logout() {
        localStorage.removeItem("smartmed_token");
        localStorage.removeItem("smartmed_user");
        setToken(null);
        setUser(null);
      },
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
