import { useState } from "react";
import { rateReading } from "../api/readings.js";

const label = (v) => (v >= 80 ? "Rất đúng" : v >= 60 ? "Khá đúng" : v >= 40 ? "Đúng một phần" : v >= 20 ? "Ít đúng" : "Không đúng");

// Người dùng chấm lời giải đúng bao nhiêu % (0-100), lưu vào database để thống kê chất lượng lời giải.
// onRated(reading): reading mới từ backend (có accuracy) để trang cha cập nhật.
export default function AccuracyRating({ reading, onRated }) {
  const saved = reading.accuracy;
  const [value, setValue] = useState(saved ?? 70);
  const [editing, setEditing] = useState(saved == null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    setBusy(true);
    setError("");
    try {
      onRated(await rateReading(reading.id, value));
      setEditing(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!editing)
    return (
      <div className="rating rating-done">
        <span>
          Bạn chấm lời giải này đúng <b>{saved}%</b> · {label(saved)}
        </span>
        <button className="btn-ghost" onClick={() => setEditing(true)}>Sửa</button>
      </div>
    );

  return (
    <div className="rating">
      <label htmlFor={`rate-${reading.id}`} className="rating-q">Lời giải này đúng với bạn bao nhiêu %?</label>
      <div className="rating-row">
        <input
          id={`rate-${reading.id}`}
          type="range"
          min={0}
          max={100}
          step={5}
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          aria-valuetext={`${value}%, ${label(value)}`}
          style={{ "--fill": `${value}%` }}
        />
        <output htmlFor={`rate-${reading.id}`} className="rating-value">
          {value}%<small>{label(value)}</small>
        </output>
        <button className="btn" onClick={save} disabled={busy}>
          {busy ? "Đang lưu…" : "Lưu đánh giá"}
        </button>
      </div>
      {error && <p className="small" style={{ color: "var(--danger)" }}>{error}</p>}
    </div>
  );
}
