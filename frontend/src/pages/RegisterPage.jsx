import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { login as apiLogin, register } from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function RegisterPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < 8) return setError("Mật khẩu tối thiểu 8 ký tự.");
    if (password !== confirm) return setError("Mật khẩu nhập lại không khớp.");
    setError("");
    setBusy(true);
    try {
      await register(email, password);
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
        <p className="muted">Tạo tài khoản mới</p>
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus /></label>
        <label>Mật khẩu<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} /></label>
        <label>Nhập lại mật khẩu<input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required /></label>
        <ErrorMessage message={error} />
        <button className="btn" disabled={busy}>{busy ? "Đang tạo..." : "Đăng ký"}</button>
        <p className="small">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p>
      </form>
    </div>
  );
}
