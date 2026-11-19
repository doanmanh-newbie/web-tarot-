import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import NavBar from "../components/NavBar.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function ProtectedRoute({ adminOnly = false }) {
  const { user, error, retry } = useAuth();
  const { pathname, hash } = useLocation();
  // Sang trang mới thì bắt đầu từ đầu trang; link có #mục thì để trang chủ tự cuộn tới mục đó
  useEffect(() => {
    if (!hash) window.scrollTo({ top: 0, behavior: "instant" }); // trang chủ bật cuộn mượt, đổi trang thì nhảy thẳng
  }, [pathname]);
  if (!user)
    return (
      <main className="container">
        {error ? <ErrorMessage message={error} onRetry={retry} /> : <LoadingState text="Đang kết nối máy chủ..." />}
      </main>
    );
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return (
    <>
      <NavBar />
      <main className="container">
        <Outlet />
      </main>
    </>
  );
}
