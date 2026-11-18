import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteReading, listReadings } from "../api/readings.js";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const PAGE = 20;

export default function HistoryPage() {
  const [items, setItems] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");

  const load = (offset = 0) => {
    setError("");
    listReadings(PAGE, offset)
      .then((list) => {
        setItems((cur) => (offset ? [...cur, ...list] : list));
        setHasMore(list.length === PAGE);
      })
      .catch((err) => setError(err.message));
  };
  useEffect(() => load(), []);

  const remove = async (r) => {
    if (!window.confirm("Xóa lần bốc này? Lưu ý: xóa sẽ KHÔNG hoàn lại lượt đã dùng.")) return;
    try {
      await deleteReading(r.id);
      setItems((cur) => cur.filter((x) => x.id !== r.id));
    } catch (err) {
      setError(err.message);
    }
  };

  if (!items) return error ? <ErrorMessage message={error} onRetry={() => load()} /> : <LoadingState />;

  return (
    <div>
      <h1>Lịch sử bốc bài</h1>
      <ErrorMessage message={error} />
      {items.length === 0 ? (
        <p className="muted">Chưa có lần bốc nào. <Link to="/#boc-bai">Bốc bài ngay</Link></p>
      ) : (
        <ul className="history">
          {items.map((r) => (
            <li key={r.id} className="panel history-item">
              <Link to={`/readings/${r.id}`} state={{ reading: r }} className="history-link">
                <strong>{r.question}</strong>
                <span className="small muted">
                  {r.spread.name} · {new Date(r.created_at).toLocaleString("vi-VN")}
                  {r.ai_status !== "done" && " · chưa có diễn giải"}
                </span>
                <span className="small">
                  {r.cards.map((c) => c.card.name_vi + (c.is_reversed ? " (ngược)" : "")).join(", ")}
                </span>
              </Link>
              <button className="btn-ghost danger" onClick={() => remove(r)}>Xóa</button>
            </li>
          ))}
        </ul>
      )}
      {hasMore && <button className="btn-ghost" onClick={() => load(items.length)}>Xem thêm</button>}
    </div>
  );
}
