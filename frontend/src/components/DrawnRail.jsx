import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import CardDetail from "./CardDetail.jsx";

const Rail3D = lazy(() => import("./Rail3D.jsx"));

// Các lá của một lần bốc trên hàng 3D (dùng ở trang bốc bài và trang kết quả).
// revealed: số lá đã lật ngửa; lá vừa lật được đưa vào giữa.
export default function DrawnRail({ reading, revealed = reading.cards.length }) {
  const [active, setActive] = useState(0);
  const [detail, setDetail] = useState(null);
  const rail = useRef(null);
  const cards = reading.cards;

  useEffect(() => {
    if (revealed > 0 && revealed <= cards.length) rail.current?.goTo(revealed - 1);
  }, [revealed, cards.length]);

  const items = cards.map((c, i) => ({ key: c.position_index, image_url: c.card.image_url, reversed: c.is_reversed, faceDown: i >= revealed }));
  const c = cards[active];
  const shown = active < revealed;

  return (
    <div className="drawn-rail">
      <div className="rail-stage small" aria-label="Các lá đã bốc, kéo ngang để xem">
        <Suspense fallback={null}>
          <Rail3D items={items} api={rail} onActive={setActive} onOpen={(i) => i < revealed && setDetail(cards[i])} />
        </Suspense>
      </div>
      {c && (
        <div className="browse-meta" aria-live="polite">
          <p className="eyebrow">
            {c.position_label} · {active + 1}/{cards.length}
          </p>
          <h2 className="browse-name">
            {shown ? c.card.name_vi : "Đang lật…"} {shown && c.is_reversed && <span className="tag">Ngược</span>}
          </h2>
          {shown && <p className="small drawn-meaning">{c.meaning}</p>}
          <div className="row-center">
            <button className="icon-btn" onClick={() => rail.current?.goTo(active - 1)} aria-label="Lá trước">‹</button>
            <button className="btn-ghost" disabled={!shown} onClick={() => setDetail(c)}>Xem chi tiết 3D</button>
            <button className="icon-btn" onClick={() => rail.current?.goTo(active + 1)} aria-label="Lá sau">›</button>
          </div>
        </div>
      )}
      <AnimatePresence>
        {detail && (
          <CardDetail
            card={detail.card}
            drawn={{ is_reversed: detail.is_reversed, meaning: detail.meaning, position_label: detail.position_label }}
            onClose={() => setDetail(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
