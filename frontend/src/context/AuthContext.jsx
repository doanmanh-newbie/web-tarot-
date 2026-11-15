import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { setAuthToken, setUnauthorizedHandler } from "../api/client.js";
import { login as apiLogin, register } from "../api/auth.js";

const AuthContext = createContext(null);

// Không có màn đăng nhập: frontend tự đăng nhập bằng tài khoản demo cấu hình trong .env
const DEMO_EMAIL = import.meta.env.VITE_DEMO_EMAIL ?? "demo@tarot.local";
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD ?? "demo-tarot-2026";

async function demoLogin() {
  try {
    return await apiLogin(DEMO_EMAIL, DEMO_PASSWORD);
  } catch (err) {
    if (err.status !== 401) throw err;
    // Lần đầu chạy: tài khoản demo chưa có thì tạo rồi đăng nhập lại
    await register(DEMO_EMAIL, DEMO_PASSWORD).catch((e) => {
      if (e.status !== 409) throw e;
    });
    return apiLogin(DEMO_EMAIL, DEMO_PASSWORD);
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { id, email, role }
  const [error, setError] = useState("");

  const connect = useCallback(() => {
    setError("");
    setUser(null);
    setAuthToken(null);
    demoLogin()
      .then((res) => {
        setAuthToken(res.access_token);
        setUser(res.user);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    connect();
    // Token hết hạn (401): đăng nhập ngầm lại
    setUnauthorizedHandler(connect);
    return () => setUnauthorizedHandler(null);
  }, [connect]);

  return <AuthContext.Provider value={{ user, error, retry: connect }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
