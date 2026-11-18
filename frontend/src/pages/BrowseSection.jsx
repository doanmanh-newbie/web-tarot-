import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { getDeck, listCatalog } from "../api/cards.js";
import CardDetail from "../components/CardDetail.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const Rail3D = lazy(() => import("../components/Rail3D.jsx"));

const PAGE = 12;
const FILTERS = [
  ["all", "Tất cả"],
  ["major", "Ẩn Chính"],
  ["wands", "Gậy"],
  ["cups", "Cốc"],
  ["swords", "Kiếm"],
  ["pentacles", "Tiền"],
  ["liked", "Đã thích"],
];
const LIKE_KEY = "tarot_liked";
const loadLiked = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem(LIKE_KEY)) ?? []);
  } catch {
    return new Set();
  }
};

// Hàng lá bài 3D tải dần: kéo/vuốt để lướt, chạm lá ở giữa để xem chi tiết
export default function BrowseSection() {
  const [cards, setCards] = useState([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const [detail, setDetail] = useState(null);
  const [liked, setLiked] = useState(loadLiked);
  const [filter, setFilter] = useState("all");
  const [allCards, setAllCards] = useState(null); // cả bộ, chỉ tải khi chọn bộ lọc
  const busy = useRef(false);
  const loaded = useRef(0);
  const rail = useRef(null);

  const loadMore = useCallback(() => {
    if (busy.current || done || error) return;
    busy.current = true;
    // Đếm theo ref: canvas gọi onNeedMore mỗi khung hình, có thể trước khi React kịp render trang vừa tải
    listCatalog(PAGE, loaded.current)
      .then((page) => {
        loaded.current += page.length;
        setCards((cur) => [...cur, ...page.filter((c) => !cur.some((x) => x.slug === c.slug))]);
        if (page.length < PAGE) setDone(true);
      })
      .catch((err) => setError(err.message))
      .finally(() => (busy.current = false));
  }, [done, error]);

  useEffect(() => {
    if (cards.length === 0) loadMore();
  }, []);

  const pick = (f) => {
    setFilter(f);
    setActive(0);
    if (f !== "all" && !allCards) getDeck().then(setAllCards).catch((err) => setError(err.message));
  };
  const keep = (c) => (filter === "liked" ? liked.has(c.slug) : filter === "major" ? c.arcana === "major" : c.suit === filter);
  const shown = filter === "all" ? cards : (allCards ?? []).filter(keep);
  const filtered = filter !== "all";
  const at = detail ? shown.findIndex((c) => c.slug === detail.slug) : -1;
  const step = (n) => {
    setDetail(shown[at + n]);
    rail.current?.goTo(at + n);
  };

  useEffect(() => {
    if (detail) return;
    const onKey = (e) => {
      if (e.key === "ArrowRight") rail.current?.goTo(active + 1);
      else if (e.key === "ArrowLeft") rail.current?.goTo(active - 1);
      else if (e.key === "Enter" && shown[active] && e.target === document.body) setDetail(shown[active]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, shown, detail]);

  const toggleLike = (slug) => {
    const next = new Set(liked);
    next.has(slug) ? next.delete(slug) : next.add(slug);
    setLiked(next);
    try {
      localStorage.setItem(LIKE_KEY, JSON.stringify([...next]));
    } catch {
      /* trình duyệt chặn lưu: vẫn giữ trong phiên */
    }
  };

  const current = shown[active];
  const skeleton = <div className="rail-skeleton" role="status" aria-label="Đang tải lá bài"><div className="skeleton" /></div>;

  return (
    <section id="bo-bai" className="section browse">
      <header className="browse-head">
        <p className="eyebrow">Rider–Waite · 78 lá</p>
        <h2 className="section-title">Bộ bài</h2>
        <div className="segmented filters" role="tablist" aria-label="Bộ lọc">
          {FILTERS.map(([f, label]) => (
            <button key={f} role="tab" aria-selected={filter === f} onClick={() => pick(f)}>
              {label}
              {f === "liked" && ` · ${liked.size}`}
            </button>
          ))}
        </div>
      </header>

      <div className="rail-stage" aria-label="Hàng lá bài 3D, kéo ngang để lướt">
        {filter === "liked" && allCards && shown.length === 0 ? (
          <div className="empty" role="status">
            <p className="empty-icon">♥</p>
            <p>Chưa có lá nào. Mở chi tiết một lá và bấm “Thích” để lưu vào đây.</p>
          </div>
        ) : shown.length === 0 ? (
          !error && skeleton
        ) : (
          <Suspense fallback={skeleton}>
            <Rail3D
              key={filter}
              items={shown.map((c) => ({ key: c.slug, image_url: c.image_url }))}
              api={rail}
              onActive={setActive}
              onOpen={(i) => setDetail(shown[i])}
              onNeedMore={filtered ? undefined : loadMore}
            />
          </Suspense>
        )}
      </div>

      <ErrorMessage message={error} onRetry={() => (setError(""), setTimeout(loadMore))} />

      <div className="browse-meta" aria-live="polite">
        {current && (
          <>
            <h3 className="browse-name">
              {current.name_vi} {liked.has(current.slug) && <span className="liked-mark" aria-label="Đã thích">♥</span>}
            </h3>
            <p className="muted small">
              {current.name} · {active + 1} / {filtered ? shown.length : 78}
            </p>
            <div className="row-center">
              <button className="icon-btn" onClick={() => rail.current?.goTo(active - 1)} aria-label="Lá trước">‹</button>
              <button className="btn-ghost" onClick={() => setDetail(current)}>Xem chi tiết 3D</button>
              <button className="icon-btn" onClick={() => rail.current?.goTo(active + 1)} aria-label="Lá sau">›</button>
            </div>
          </>
        )}
      </div>
      <p className="hint">Kéo hoặc vuốt ngang để lướt · chạm lá ở giữa để xem chi tiết</p>

      <AnimatePresence>
        {detail && (
          <CardDetail
            card={detail}
            liked={liked.has(detail.slug)}
            onToggleLike={() => toggleLike(detail.slug)}
            onPrev={at > 0 ? () => step(-1) : undefined}
            onNext={at >= 0 && at < shown.length - 1 ? () => step(1) : undefined}
            onClose={() => setDetail(null)}
          />
        )}
      </AnimatePresence>
    </section>
  );
}
