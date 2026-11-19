import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { getDeck } from "../api/cards.js";
import CardDetail from "../components/CardDetail.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const Rail3D = lazy(() => import("../components/Rail3D.jsx"));

const SHUFFLE_MS = 1600;
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
const shuffle = (arr) => {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = crypto.getRandomValues(new Uint32Array(1))[0] % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
};

// Hàng lá bài 3D nối vòng: kéo/vuốt để lướt mãi, chạm lá ở giữa để xem chi tiết, Xáo bài để trộn thứ tự
export default function BrowseSection() {
  const [deck, setDeck] = useState(null);
  const [order, setOrder] = useState(null); // thứ tự sau khi xáo; null = thứ tự gốc
  const [spinning, setSpinning] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const [detail, setDetail] = useState(null);
  const [liked, setLiked] = useState(loadLiked);
  const [filter, setFilter] = useState("all");
  const rail = useRef(null);

  const load = () => {
    setError("");
    getDeck().then(setDeck).catch((err) => setError(err.message));
  };
  useEffect(load, []);

  const pick = (f) => {
    setFilter(f);
    setOrder(null);
    setActive(0);
  };
  const keep = (c) =>
    filter === "all" || (filter === "liked" ? liked.has(c.slug) : filter === "major" ? c.arcana === "major" : c.suit === filter);
  const base = (deck ?? []).filter(keep);
  const shown = order ? order.map((slug) => base.find((c) => c.slug === slug)).filter(Boolean) : base;
  const at = detail ? shown.findIndex((c) => c.slug === detail.slug) : -1;
  const step = (n) => {
    const i = (at + n + shown.length) % shown.length;
    setDetail(shown[i]);
    rail.current?.goTo(i);
  };

  // Xào bài: cả hàng cuộn thành vòng tròn xoay nhanh, rồi trải lại theo thứ tự ngẫu nhiên
  const doShuffle = () => {
    if (spinning || base.length < 2) return;
    setSpinning(true);
    setTimeout(() => {
      setOrder(shuffle(base.map((c) => c.slug)));
      setSpinning(false);
      rail.current?.goTo(0);
    }, SHUFFLE_MS);
  };

  useEffect(() => {
    if (detail || spinning) return;
    const onKey = (e) => {
      if (e.target !== document.body) return;
      if (e.key === "ArrowRight") rail.current?.goTo(active + 1);
      else if (e.key === "ArrowLeft") rail.current?.goTo(active - 1);
      else if (e.key === "Enter" && shown[active]) setDetail(shown[active]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, shown, detail, spinning]);

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
        <div className="browse-tools">
          <div className="segmented filters" role="tablist" aria-label="Bộ lọc">
            {FILTERS.map(([f, label]) => (
              <button key={f} role="tab" aria-selected={filter === f} onClick={() => pick(f)}>
                {label}
                {f === "liked" && ` · ${liked.size}`}
              </button>
            ))}
          </div>
          <button className="btn-ghost shuffle-btn" onClick={doShuffle} disabled={spinning || base.length < 2}>
            ⟳ {spinning ? "Đang xáo…" : "Xáo bài"}
          </button>
        </div>
      </header>

      <div className="rail-stage browse-stage" aria-label="Hàng lá bài 3D, kéo ngang để lướt">
        {filter === "liked" && deck && shown.length === 0 ? (
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
              loop
              mode={spinning ? "ring" : "rail"}
              items={shown.map((c) => ({ key: c.slug, image_url: c.image_url }))}
              api={rail}
              onActive={setActive}
              onOpen={(i) => setDetail(shown[i])}
            />
          </Suspense>
        )}
      </div>

      <ErrorMessage message={error} onRetry={load} />

      <div className="browse-meta" aria-live="polite">
        {current && (
          <h3 className="browse-name">
            {current.name_vi} {liked.has(current.slug) && <span className="liked-mark" aria-label="Đã thích">♥</span>}
          </h3>
        )}
      </div>
      {current?.upright_meaning && (
        <div className="browse-info">
          <div className="panel">
            <h3>Xuôi</h3>
            <p>{current.upright_meaning}</p>
          </div>
          <div className="panel">
            <h3>Ngược</h3>
            <p>{current.reversed_meaning}</p>
          </div>
        </div>
      )}

      <AnimatePresence>
        {detail && (
          <CardDetail
            card={detail}
            liked={liked.has(detail.slug)}
            onToggleLike={() => toggleLike(detail.slug)}
            onPrev={shown.length > 1 ? () => step(-1) : undefined}
            onNext={shown.length > 1 ? () => step(1) : undefined}
            onClose={() => setDetail(null)}
          />
        )}
      </AnimatePresence>
    </section>
  );
}
