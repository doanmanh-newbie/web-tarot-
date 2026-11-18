import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

// three.js chỉ tải khi mở chi tiết, trang lướt bài vẫn nhẹ
const CardModel3D = lazy(() => import("./CardModel3D.jsx"));

const SUIT_VI = { wands: "Bộ Gậy", cups: "Bộ Cốc", swords: "Bộ Kiếm", pentacles: "Bộ Tiền" };
const arcanaLabel = (c) =>
  c.arcana === "major" ? `Ẩn Chính · ${c.number}` : c.suit ? `${SUIT_VI[c.suit]} · ${c.number}` : "";

// Lớp xem chi tiết: lá bay từ hàng ra giữa (layoutId), rồi thay bằng mô hình 3D kéo xoay được.
// drawn: { is_reversed, meaning, position_label } khi xem lá vừa bốc; không có thì hiện cả nghĩa xuôi & ngược.
export default function CardDetail({ card, drawn, layoutId, liked, onToggleLike, onClose }) {
  const [ready, setReady] = useState(false);
  const controls = useRef(null);
  const closeRef = useRef(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose; // trang cha truyền hàm mới mỗi lần render; không để effect chạy lại

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e) => e.key === "Escape" && onCloseRef.current();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const reversed = !!drawn?.is_reversed;

  return (
    <motion.div
      className="detail-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={card.name_vi}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <div className="detail" onClick={(e) => e.stopPropagation()}>
        <button ref={closeRef} className="icon-btn detail-close" onClick={onClose} aria-label="Đóng">
          ✕
        </button>

        <div className="detail-stage">
          <motion.img
            layoutId={layoutId}
            src={card.image_url}
            alt=""
            draggable={false}
            className={`stage-img ${reversed ? "reversed" : ""}`}
            animate={{ opacity: ready ? 0 : 1 }}
            transition={{ opacity: { duration: 0.3 } }}
          />
          <Suspense fallback={null}>
            <CardModel3D card={card} reversed={reversed} controls={controls} onReady={() => setReady(true)} />
          </Suspense>
          <p className="stage-hint">Kéo lá để xoay 360°</p>
        </div>

        <motion.div
          className="detail-info"
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <p className="eyebrow">{drawn?.position_label ?? arcanaLabel(card)}</p>
          <h2 className="detail-title">
            {card.name_vi} {reversed && <span className="tag">Ngược</span>}
          </h2>
          <p className="muted small">{card.name}</p>
          <hr className="rule" />
          {drawn ? (
            <p>{drawn.meaning}</p>
          ) : (
            <>
              <h3>Xuôi</h3>
              <p>{card.upright_meaning}</p>
              <h3>Ngược</h3>
              <p>{card.reversed_meaning}</p>
            </>
          )}
          <div className="detail-actions">
            {onToggleLike && (
              <button className={`btn-ghost ${liked ? "liked" : ""}`} onClick={onToggleLike} aria-pressed={!!liked}>
                {liked ? "♥ Đã thích" : "♡ Thích"}
              </button>
            )}
            <button className="icon-btn" onClick={() => controls.current?.spin(-7)} aria-label="Xoay sang trái">⟲</button>
            <button className="icon-btn" onClick={() => controls.current?.spin(7)} aria-label="Xoay sang phải">⟳</button>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
