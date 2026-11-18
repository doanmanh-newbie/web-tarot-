import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import NavBar from "../components/NavBar.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function ProtectedRoute({ adminOnly = false }) {
  const { user, error, retry } = useAuth();
  if (!user)
    return (
      <main className="container">
        {error ? <ErrorMessage message={error} onRetry={retry} /> : <LoadingState text="Đang kết nối máy chủ..." />}
      </main>
    );
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return (
    <>
      <main className="container">
        <Outlet />
      </main>
      <NavBar />
    </>
  );
}
