import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import HomePage from "./pages/HomePage.jsx";
import ReadingResultPage from "./pages/ReadingResultPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import AdminCardsPage from "./pages/AdminCardsPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/draw" element={<Navigate to={{ pathname: "/", hash: "#boc-bai" }} replace />} />
        <Route path="/readings/:id" element={<ReadingResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
      <Route element={<ProtectedRoute adminOnly />}>
        <Route path="/admin/cards" element={<AdminCardsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
