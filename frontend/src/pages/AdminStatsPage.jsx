import { useEffect, useState } from "react";
import { getAccuracyStats } from "../api/admin.js";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const RANGES = [7, 30, 90];
const pct = (v) => (v == null ? "–" : `${Math.round(v)}%`);
const dayLabel = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });

function Tile({ label, value, note }) {
  return (
    <div className="stat-tile">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {note && <p className="stat-note">{note}</p>}
    </div>
  );
}

// Thanh ngang: độ dài = độ đúng trung bình của nhóm; số lượt chấm ghi kèm để biết nhóm nào đủ tin cậy
function GroupBars({ title, items }) {
  return (
    <section className="panel stat-card">
      <h2>{title}</h2>
      {items.length === 0 ? (
        <p className="muted small">Chưa có lượt chấm.</p>
      ) : (
        <table className="hbars">
          <thead className="sr-only">
            <tr>
              <th>Nhóm</th>
              <th>Độ đúng trung bình</th>
              <th>Số lượt chấm</th>
            </tr>
          </thead>
          <tbody>
            {items.map((g) => (
              <tr key={g.name} title={`${g.name}: ${pct(g.average)} trung bình từ ${g.rated} lượt chấm`}>
                <th scope="row">{g.name}</th>
                <td className="hbar-cell">
                  <span className="hbar" style={{ width: `${g.average ?? 0}%` }} />
                  <b>{pct(g.average)}</b>
                </td>
                <td className="muted small">{g.rated} lượt</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

// Cột đứng theo ngày: chiều cao = độ đúng trung bình; rê chuột/focus để xem chi tiết
function DailyChart({ days }) {
  const [hover, setHover] = useState(null);
  const shown = hover ?? [...days].reverse().find((d) => d.rated) ?? null;
  const every = Math.ceil(days.length / 10); // nhãn trục ngày thưa ra để không chồng chữ
  return (
    <section className="panel stat-card stat-wide">
      <div className="stat-head">
        <h2>Độ đúng theo ngày</h2>
        <p className="muted small" aria-live="polite">
          {shown ? `${dayLabel(shown.day)} · ${pct(shown.average)} · ${shown.rated} lượt chấm` : "Chưa có lượt chấm trong khoảng này"}
        </p>
      </div>
      <div className="vbars" role="list" onMouseLeave={() => setHover(null)}>
        {days.map((d, i) => (
          <div
            key={d.day}
            role="listitem"
            tabIndex={0}
            className={`vbar-col ${hover?.day === d.day ? "on" : ""}`}
            aria-label={`${dayLabel(d.day)}: ${d.rated ? `${pct(d.average)}, ${d.rated} lượt chấm` : "không có lượt chấm"}`}
            onMouseEnter={() => setHover(d)}
            onFocus={() => setHover(d)}
            onBlur={() => setHover(null)}
          >
            <span className={`vbar ${d.rated ? "" : "empty"}`} style={{ height: d.rated ? `${d.average}%` : undefined }} />
            <span className="vbar-x">{i % every === 0 || i === days.length - 1 ? dayLabel(d.day) : ""}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

// Thống kê độ đúng do người dùng tự chấm cho lời giải AI (chỉ admin)
export default function AdminStatsPage() {
  const [days, setDays] = useState(30);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    getAccuracyStats(days)
      .then(setStats)
      .catch((err) => setError(err.message));
  };
  useEffect(load, [days]);

  if (!stats) return error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />;

  const maxBucket = Math.max(1, ...stats.buckets.map((b) => b.rated));
  return (
    <div className="stats-page">
      <header className="page-head">
        <div>
          <p className="eyebrow left">Quản trị</p>
          <h1>Thống kê độ đúng</h1>
          <p className="muted small">Người dùng tự chấm lời giải đúng bao nhiêu % với họ. Số liệu của mọi người dùng, chỉ tính lời giải chưa xóa.</p>
        </div>
        <div className="segmented" role="radiogroup" aria-label="Khoảng thời gian của biểu đồ theo ngày">
          {RANGES.map((r) => (
            <button key={r} role="radio" aria-checked={days === r} aria-selected={days === r} onClick={() => setDays(r)}>
              {r} ngày
            </button>
          ))}
        </div>
      </header>
      <ErrorMessage message={error} />

      <div className="stat-tiles">
        <Tile label="Độ đúng trung bình" value={pct(stats.average)} note={`từ ${stats.rated} lượt chấm`} />
        <Tile label="Lượt đã chấm" value={stats.rated} note={`trên ${stats.interpreted} lời giải`} />
        <Tile label="Tỉ lệ được chấm" value={`${stats.rating_rate}%`} note="lời giải có người chấm điểm" />
      </div>

      <div className="stat-grid">
        <DailyChart days={stats.by_day} />

        <section className="panel stat-card">
          <h2>Phân bố điểm</h2>
          <div className="dist" role="list">
            {stats.buckets.map((b) => (
              <div key={b.name} className="dist-col" role="listitem" aria-label={`${b.name}: ${b.rated} lượt`} title={`${b.name}: ${b.rated} lượt`}>
                <span className="dist-n">{b.rated}</span>
                <span className="dist-bar" style={{ height: `${(b.rated / maxBucket) * 100}%` }} />
                <span className="dist-x">{b.name}</span>
              </div>
            ))}
          </div>
        </section>

        <GroupBars title="Theo phiên bản prompt (trước / sau khi sửa)" items={stats.by_version ?? []} />
        <GroupBars title="Theo kiểu trải bài" items={stats.by_spread} />
        <GroupBars title="Theo chủ đề" items={stats.by_topic} />
        <GroupBars title="Theo đối tượng người hỏi" items={stats.by_persona} />
      </div>
    </div>
  );
}
