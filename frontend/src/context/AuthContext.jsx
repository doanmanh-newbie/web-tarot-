import { createContext, useContext, useEffect, useState } from "react";
import { setAuthToken, setUnauthorizedHandler } from "../api/client.js";

const AuthContext = createContext(null);
const KEY = "tarot_auth";

function loadSaved() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    if (saved?.token) {
      setAuthToken(saved.token);
      return saved.user;
    }
  } catch {
    /* localStorage bị chặn: bỏ qua, đăng nhập lại */
  }
  return null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadSaved); // { id, email, role }

  const login = (token, userInfo) => {
    setAuthToken(token);
    setUser(userInfo);
    try {
      localStorage.setItem(KEY, JSON.stringify({ token, user: userInfo }));
    } catch {
      /* ignore */
    }
  };
  const logout = () => {
    setAuthToken(null);
    setUser(null);
    try {
      localStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  };

  // Token hết hạn/không hợp lệ: đăng xuất, ProtectedRoute sẽ đưa về /login
  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, []);

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
