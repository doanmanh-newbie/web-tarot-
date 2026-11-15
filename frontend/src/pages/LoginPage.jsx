import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { login as apiLogin } from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await apiLogin(email, password);
      login(res.access_token, res.user);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="panel auth-form" onSubmit={submit}>
        <h1>✦ Tarot</h1>
        <p className="muted">Đăng nhập để bốc bài</p>
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus /></label>
        <label>Mật khẩu<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
        <ErrorMessage message={error} />
        <button className="btn" disabled={busy}>{busy ? "Đang đăng nhập..." : "Đăng nhập"}</button>
        <p className="small">Chưa có tài khoản? <Link to="/register">Đăng ký</Link></p>
      </form>
    </div>
  );
}
