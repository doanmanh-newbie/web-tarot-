import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const SECTIONS = [
  { id: "bo-bai", icon: "❖", label: "Bộ bài" },
  { id: "boc-bai", icon: "✦", label: "Bốc bài" },
];

// Phần nào của trang chủ đang chiếm giữa màn hình thì sáng tab đó
function useCurrentSection(enabled) {
  const [current, setCurrent] = useState("");
  useEffect(() => {
    if (!enabled) return setCurrent("");
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setCurrent(e.target.id)),
      { rootMargin: "-45% 0px -45% 0px" },
    );
    ["top", ...SECTIONS.map((s) => s.id), "kieu-trai"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) io.observe(el);
    });
    return () => io.disconnect();
  }, [enabled]);
  return current;
}

// Thanh điều hướng dưới cùng kiểu app di động; trên trang chủ các tab cuộn tới từng phần
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

  return (
    <nav className="tabbar" aria-label="Điều hướng chính">
      {SECTIONS.map((s) => (
        <Link
          key={s.id}
          to={`/#${s.id}`}
          onClick={(e) => go(e, s.id)}
          className={`${s.id === "boc-bai" ? "tab-draw" : ""} ${current === s.id ? "active" : ""}`}
          aria-current={current === s.id ? "location" : undefined}
        >
          <span aria-hidden="true">{s.icon}</span>
          {s.label}
        </Link>
      ))}
      <NavLink to="/history">
        <span aria-hidden="true">☾</span>Lịch sử
      </NavLink>
      {user.role === "admin" && (
        <NavLink to="/admin/cards">
          <span aria-hidden="true">✎</span>Quản lý
        </NavLink>
      )}
    </nav>
  );
}
