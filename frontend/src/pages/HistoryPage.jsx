import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteReading, listReadings } from "../api/readings.js";
import { getDeck } from "../api/cards.js";
import { loadLocalHistory, removeLocalHistory } from "../api/localHistory.js";
import { YES_NO_VI } from "../components/CardDetail.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const PAGE = 20;
const KIND_VI = { reading: "Hỏi bài", day: "Lá hôm nay", week: "Lá tuần này", month: "Lá tháng này", year: "Lá năm nay", yesno: "Yes/No" };
const FILTERS = [["all", "Tất cả"], ...Object.entries(KIND_VI)];
const when = (iso) => new Date(iso).toLocaleString("vi-VN", { dateStyle: "medium", timeStyle: "short" });

function CardThumbs({ cards }) {
  return (
    <ul className="h-cards">
      {cards.map((c, i) => (
        <li key={i}>
          <img className={c.reversed ? "reversed" : ""} src={c.image_url} alt="" loading="lazy" />
          {c.label && <span className="slot-label">{c.label}</span>}
          <span className="h-card-name">{c.name}</span>
          {c.reversed && <span className="tag">Ngược</span>}
        </li>
      ))}
    </ul>
  );
}

// Lịch sử đầy đủ: lần bốc có lời giải AI (lưu trên tài khoản) + lần rút nhanh theo kỳ, Yes/No (lưu trên thiết bị)
export default function HistoryPage() {
  const [readings, setReadings] = useState(null);
  const [local, setLocal] = useState(loadLocalHistory);
  const [deck, setDeck] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

  const load = (offset = 0) => {
    setError("");
    listReadings(PAGE, offset)
      .then((list) => {
        setReadings((cur) => (offset ? [...cur, ...list] : list));
        setHasMore(list.length === PAGE);
      })
      .catch((err) => setError(err.message));
  };
  useEffect(() => {
    load();
    getDeck().then(setDeck).catch(() => {}); // chỉ để hiện hình lá của lần rút nhanh
  }, []);

  const remove = async (item) => {
    if (item.kind !== "reading") {
      if (!window.confirm("Xóa lần rút này khỏi lịch sử trên máy?")) return;
      removeLocalHistory(item.id);
      return setLocal(loadLocalHistory());
    }
    if (!window.confirm("Xóa lần bốc này? Lưu ý: xóa sẽ KHÔNG hoàn lại lượt đã dùng.")) return;
    try {
      await deleteReading(item.id);
      setReadings((cur) => cur.filter((x) => x.id !== item.id));
    } catch (err) {
      setError(err.message);
    }
  };

  if (!readings) return error ? <ErrorMessage message={error} onRetry={() => load()} /> : <LoadingState />;

  const bySlug = (slug) => deck.find((c) => c.slug === slug);
  // shortcut: lịch sử server tải theo trang còn rút nhanh có sẵn hết, nên thứ tự chỉ đúng trong phần đã tải; đủ dùng khi ít lượt
  const items = [
    ...readings.map((r) => ({ ...r, kind: "reading" })),
    // Bản ghi cũ chỉ có 1 lá (slug, reversed); bản mới có cards[] khi bốc 1/3/5 lá
    ...local.map((e) => ({ ...e, picks: (e.cards ?? [{ slug: e.slug, reversed: e.reversed }]).map((c) => ({ ...c, card: bySlug(c.slug) })) })),
  ]
    .filter((x) => filter === "all" || x.kind === filter)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const count = (k) => (k === "all" ? readings.length + local.length : k === "reading" ? readings.length : local.filter((e) => e.kind === k).length);

  return (
    <div className="history-page">
      <header className="page-head">
        <div>
          <p className="eyebrow left">Nhật ký tarot</p>
          <h1>Lịch sử bốc bài</h1>
        </div>
        <Link className="btn" to="/hoi-bai">✦ Hỏi bài mới</Link>
      </header>
      <div className="segmented filters left" role="tablist" aria-label="Lọc theo mục">
        {FILTERS.map(([k, label]) => (
          <button key={k} role="tab" aria-selected={filter === k} onClick={() => setFilter(k)}>
            {label} · {count(k)}
          </button>
        ))}
      </div>
      <ErrorMessage message={error} />

      {items.length === 0 ? (
        <div className="empty history-empty" role="status">
          <p className="empty-icon">☾</p>
          <p>Chưa có lần bốc nào trong mục này.</p>
          <Link to="/#boc-bai">Bốc một lá ngay</Link>
        </div>
      ) : (
        <ul className="history">
          {items.map((x) => (
            <li key={`${x.kind}-${x.id}`} className="panel history-item">
              <div className="h-head">
                <span className="tag">{KIND_VI[x.kind]}{x.kind === "reading" && ` · ${x.spread.name}`}</span>
                {x.accuracy != null && <span className="tag accuracy-tag">Đúng {x.accuracy}%</span>}
                <time className="small muted" dateTime={x.created_at}>{when(x.created_at)}</time>
              </div>

              {x.kind === "reading" ? (
                <>
                  <p className="question">“{x.question}”</p>
                  <CardThumbs
                    cards={x.cards.map((c) => ({ image_url: c.card.image_url, name: c.card.name_vi, label: c.position_label, reversed: c.is_reversed }))}
                  />
                  {x.ai_status === "done" ? (
                    <details className="h-interp">
                      <summary>Lời diễn giải</summary>
                      <p className="pre-wrap small">{x.ai_interpretation}</p>
                    </details>
                  ) : (
                    <p className="small muted">Chưa có lời diễn giải, mở lần bốc để giải lại.</p>
                  )}
                </>
              ) : (
                <>
                  {x.period && <p className="small muted">{x.period}</p>}
                  {x.question && <p className="question">“{x.question}”</p>}
                  {x.picks.every((p) => p.card) ? (
                    <div className="h-local">
                      <CardThumbs cards={x.picks.map((p) => ({ image_url: p.card.image_url, name: p.card.name_vi, label: p.label, reversed: p.reversed }))} />
                      <div>
                        {x.kind === "yesno" && x.picks[0].card.details && (
                          <p className={`yn-answer small-yn ${x.picks[0].card.details.yes_no[x.picks[0].reversed ? "reversed" : "upright"]}`}>
                            {YES_NO_VI[x.picks[0].card.details.yes_no[x.picks[0].reversed ? "reversed" : "upright"]]}
                          </p>
                        )}
                        {x.picks.map((p, i) => (
                          <p key={i} className="small">
                            {x.picks.length > 1 && <b>{p.label ?? `Lá ${i + 1}`}: </b>}
                            {p.reversed ? p.card.reversed_meaning : p.card.upright_meaning}
                          </p>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="small muted">Đang tải lá bài…</p>
                  )}
                </>
              )}

              <div className="h-actions">
                {x.kind === "reading" && (
                  <Link className="btn-ghost" to={`/readings/${x.id}`} state={{ reading: x }}>Mở lần bốc</Link>
                )}
                <button className="btn-ghost danger" onClick={() => remove(x)}>Xóa</button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {hasMore && (filter === "all" || filter === "reading") && (
        <div className="row-center">
          <button className="btn-ghost" onClick={() => load(readings.length)}>Xem thêm</button>
        </div>
      )}
    </div>
  );
}
