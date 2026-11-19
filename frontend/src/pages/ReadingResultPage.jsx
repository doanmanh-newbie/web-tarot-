import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getReading, reinterpret } from "../api/readings.js";
import DrawnRail from "../components/DrawnRail.jsx";
import Interpretation from "../components/Interpretation.jsx";
import AccuracyRating from "../components/AccuracyRating.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function ReadingResultPage() {
  const { id } = useParams();
  const { state } = useLocation();
  // Vừa bốc xong thì trang trước đã truyền sẵn reading, khỏi gọi lại API
  const [reading, setReading] = useState(state?.reading?.id === Number(id) ? state.reading : null);
  const [error, setError] = useState("");
  const [retrying, setRetrying] = useState(false);

  const load = () => {
    setError("");
    getReading(id).then(setReading).catch((err) => setError(err.message));
  };
  useEffect(() => {
    if (!reading) load();
  }, [id]);

  const retry = async () => {
    setError("");
    setRetrying(true);
    try {
      setReading(await reinterpret(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setRetrying(false);
    }
  };

  if (!reading) return error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{reading.spread.name}</h1>
          <p className="muted small">{new Date(reading.created_at).toLocaleString("vi-VN")}</p>
        </div>
        <Link className="btn-ghost" to="/hoi-bai">Hỏi câu khác</Link>
      </div>
      <blockquote className="question">“{reading.question}”</blockquote>

      <DrawnRail reading={reading} />

      <section className="panel interpretation">
        <h2>Lời diễn giải</h2>
        {retrying ? (
          <LoadingState text="Đang diễn giải lại..." />
        ) : reading.ai_status === "done" ? (
          <>
            <Interpretation text={reading.ai_interpretation} />
            <AccuracyRating reading={reading} onRated={setReading} />
          </>
        ) : (
          <div>
            <p className="muted">Chưa có lời diễn giải (AI đang bận hoặc gặp lỗi). Thử lại không tốn thêm lượt.</p>
            <button className="btn" onClick={retry}>Giải lại</button>
          </div>
        )}
        <ErrorMessage message={error} />
      </section>

      <p className="disclaimer small muted">{reading.disclaimer}</p>
    </div>
  );
}
