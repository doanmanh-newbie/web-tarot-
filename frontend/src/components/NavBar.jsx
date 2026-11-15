import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="navbar">
      <NavLink to="/" className="brand">✦ Tarot</NavLink>
      <nav>
        <NavLink to="/" end>Bốc bài</NavLink>
        <NavLink to="/history">Lịch sử</NavLink>
        {user.role === "admin" && <NavLink to="/admin/cards">Quản lý bài</NavLink>}
      </nav>
      <div className="nav-user">
        <span className="muted">{user.email}</span>
        <button className="btn-ghost" onClick={() => { logout(); navigate("/login"); }}>Đăng xuất</button>
      </div>
    </header>
  );
}
