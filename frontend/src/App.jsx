import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import SpreadSelectPage from "./pages/SpreadSelectPage.jsx";
import ReadingResultPage from "./pages/ReadingResultPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import AdminCardsPage from "./pages/AdminCardsPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<SpreadSelectPage />} />
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
