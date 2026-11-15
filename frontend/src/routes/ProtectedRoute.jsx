import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import NavBar from "../components/NavBar.jsx";

export default function ProtectedRoute({ adminOnly = false }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
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
