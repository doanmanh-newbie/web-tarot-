import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import HomePage from "./pages/HomePage.jsx";
import AskPage from "./pages/AskPage.jsx";
import ReadingResultPage from "./pages/ReadingResultPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import AdminCardsPage from "./pages/AdminCardsPage.jsx";
import AdminStatsPage from "./pages/AdminStatsPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/hoi-bai" element={<AskPage />} />
        <Route path="/draw" element={<Navigate to="/hoi-bai" replace />} />
        <Route path="/readings/:id" element={<ReadingResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
      <Route element={<ProtectedRoute adminOnly />}>
        <Route path="/admin/cards" element={<AdminCardsPage />} />
        <Route path="/admin/stats" element={<AdminStatsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
