import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const SECTIONS = [
  { id: "bo-bai", icon: "❖", label: "Bộ bài" },
  { id: "boc-bai", icon: "☀", label: "Bốc bài" },
];
// Thanh trên cùng có thêm các mục phụ của trang chủ
const TOP_SECTIONS = [...SECTIONS, { id: "kieu-trai", label: "Kiểu trải" }, { id: "hoi-dap", label: "Hỏi đáp" }];

// Phần nào của trang chủ đang chiếm giữa màn hình thì sáng tab đó
function useCurrentSection(enabled) {
  const [current, setCurrent] = useState("");
  useEffect(() => {
    if (!enabled) return setCurrent("");
    const io = new IntersectionObserver((entries) => entries.forEach((e) => e.isIntersecting && setCurrent(e.target.id)), {
      rootMargin: "-45% 0px -45% 0px",
    });
    ["top", ...TOP_SECTIONS.map((s) => s.id)].forEach((id) => {
      const el = document.getElementById(id);
      if (el) io.observe(el);
    });
    return () => io.disconnect();
  }, [enabled]);
  return current;
}

// Thanh trên cùng (màn rộng) + thanh dưới kiểu app di động (màn hẹp); trên trang chủ các mục cuộn tới từng phần
export default function NavBar() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const onHome = pathname === "/";
  const current = useCurrentSection(onHome);

  const go = (e, id) => {
    if (!onHome) return; // trang khác: để Link chuyển về /#id, trang chủ tự cuộn
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const link = (s, className = "") => (
    <Link
      key={s.id}
      to={`/#${s.id}`}
      onClick={(e) => go(e, s.id)}
      className={`${className} ${current === s.id ? "active" : ""}`}
      aria-current={current === s.id ? "location" : undefined}
    >
      {s.icon && <span aria-hidden="true">{s.icon}</span>}
      {s.label}
    </Link>
  );

  return (
    <>
      <header className="topbar">
        <Link to="/#top" className="topbar-brand" onClick={(e) => go(e, "top")}>
          ✦ Tarot
        </Link>
        <nav className="topbar-links" aria-label="Các mục">
          {TOP_SECTIONS.map((s) => link(s))}
          <NavLink to="/history">Lịch sử</NavLink>
          {user.role === "admin" && <NavLink to="/admin/cards">Quản lý</NavLink>}
          {user.role === "admin" && <NavLink to="/admin/stats">Thống kê</NavLink>}
        </nav>
        <Link to="/hoi-bai" className="btn topbar-cta">
          ✦ Hỏi bài
        </Link>
      </header>
      <nav className="tabbar" aria-label="Điều hướng chính">
        {SECTIONS.map((s) => link(s))}
        <NavLink to="/hoi-bai" className="tab-draw">
          <span aria-hidden="true">✧</span>Hỏi bài
        </NavLink>
        <NavLink to="/history">
          <span aria-hidden="true">☾</span>Lịch sử
        </NavLink>
        {user.role === "admin" && (
          <NavLink to="/admin/cards">
            <span aria-hidden="true">✎</span>Quản lý
          </NavLink>
        )}
      </nav>
    </>
  );
}
