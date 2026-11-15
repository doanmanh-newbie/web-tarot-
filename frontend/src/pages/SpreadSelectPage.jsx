import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listSpreads } from "../api/spreads.js";
import { getQuota } from "../api/quota.js";
import { createReading } from "../api/readings.js";
import QuotaBadge from "../components/QuotaBadge.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

export default function SpreadSelectPage() {
  const navigate = useNavigate();
  const [spreads, setSpreads] = useState(null);
  const [quota, setQuota] = useState(null);
  const [selected, setSelected] = useState(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [drawing, setDrawing] = useState(false);

  const load = () => {
    setError("");
    Promise.all([listSpreads(), getQuota()])
      .then(([s, q]) => {
        setSpreads(s);
        setQuota(q);
        setSelected((cur) => cur ?? s[0]?.id ?? null);
      })
      .catch((err) => setError(err.message));
  };
  useEffect(load, []);

  const draw = async (e) => {
    e.preventDefault();
    if (!question.trim()) return setError("Hãy nhập câu hỏi của bạn.");
    setError("");
    setDrawing(true);
    try {
      const reading = await createReading(selected, question.trim());
      navigate(`/readings/${reading.id}`, { state: { reading } });
    } catch (err) {
      setError(err.message);
      getQuota().then(setQuota).catch(() => {});
      setDrawing(false);
    }
  };

  if (drawing) return <LoadingState text="Đang xào bài và diễn giải... (có thể mất tới 20 giây)" />;
  if (!spreads) return error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />;

  const outOfQuota = quota && !quota.unlimited && quota.remaining === 0;

  return (
    <form onSubmit={draw}>
      <div className="page-head">
        <h1>Bốc bài</h1>
        <QuotaBadge quota={quota} />
      </div>

      <h2>1. Chọn kiểu trải bài</h2>
      <div className="spread-grid">
        {spreads.map((s) => (
          <button
            type="button"
            key={s.id}
            className={`panel spread-option ${selected === s.id ? "active" : ""}`}
            onClick={() => setSelected(s.id)}
            aria-pressed={selected === s.id}
          >
            <div className="spread-title">
              <strong>{s.name}</strong>
              <span className="tag">{s.card_count} lá</span>
            </div>
            <p className="small muted">{s.description}</p>
            <div className="small">{s.positions.map((p) => p.label).join(" · ")}</div>
          </button>
        ))}
      </div>

      <h2>2. Câu hỏi của bạn</h2>
      <textarea
        rows={3}
        maxLength={300}
        placeholder="Ví dụ: Công việc sắp tới của tôi thế nào?"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        aria-label="Câu hỏi"
      />
      <div className="small muted right">{question.length}/300</div>

      <ErrorMessage message={error} />
      {outOfQuota && <p className="muted">Bạn đã dùng hết lượt hôm nay. Hãy quay lại sau giờ làm mới.</p>}
      <button className="btn btn-lg" disabled={!selected || outOfQuota}>✦ Bốc bài</button>
    </form>
  );
}
