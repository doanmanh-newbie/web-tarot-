import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { getDeck } from "../api/cards.js";

// three.js chỉ tải khi mở chi tiết, trang lướt bài vẫn nhẹ
const CardModel3D = lazy(() => import("./CardModel3D.jsx"));

const SUIT_VI = { wands: "Bộ Gậy", cups: "Bộ Cốc", swords: "Bộ Kiếm", pentacles: "Bộ Tiền" };
const arcanaLabel = (c) =>
  c.arcana === "major" ? `Ẩn Chính · ${c.number}` : c.suit ? `${SUIT_VI[c.suit]} · ${c.number}` : "";
export const YES_NO_VI = { yes: "Có", no: "Không", maybe: "Có thể" };
const TOPICS = [
  ["love", "Tình cảm"],
  ["career", "Công việc"],
  ["finance", "Tài chính"],
  ["health", "Sức khỏe"],
];
const TABS = ["Tổng quan", "Chủ đề", "Lời khuyên"];

// Lá trong lần bốc chỉ có tóm tắt (không có details): lấy bản đầy đủ từ cả bộ
function useFullCard(card) {
  const [full, setFull] = useState(card.details ? card : null);
  useEffect(() => {
    if (card.details) return setFull(card);
    setFull(null);
    let alive = true;
    getDeck()
      .then((all) => alive && setFull(all.find((c) => c.slug === card.slug) ?? null))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [card]);
  return full;
}

// Xuôi + ngược, hoặc chỉ chiều vừa bốc
function Both({ pair, only }) {
  if (only) return <p>{pair[only]}</p>;
  return (
    <>
      <p><span className="dir">Xuôi</span> {pair.upright}</p>
      <p><span className="dir">Ngược</span> {pair.reversed}</p>
    </>
  );
}

// Lớp xem chi tiết: lá bay từ hàng ra giữa (layoutId), rồi thay bằng mô hình 3D kéo xoay được.
// drawn: { is_reversed, meaning, position_label } khi xem lá vừa bốc; không có thì hiện cả nghĩa xuôi & ngược.
// onPrev/onNext: chuyển sang lá trước/sau mà không đóng lớp chi tiết (trang lướt bài)
export default function CardDetail({ card, drawn, layoutId, liked, onToggleLike, onPrev, onNext, onClose }) {
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState(0);
  const full = useFullCard(card);
  const d = full?.details;
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
  const only = drawn ? (reversed ? "reversed" : "upright") : null;

  useEffect(() => setReady(false), [card.slug]);

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
            <CardModel3D key={card.slug} card={card} reversed={reversed} controls={controls} onReady={() => setReady(true)} />
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
          {d && (
            <ul className="facts">
              <li>Nguyên tố · {d.element}</li>
              {d.astrology && <li>Chiêm tinh · {d.astrology}</li>}
              <li>
                Yes/No · {only ? YES_NO_VI[d.yes_no[only]] : `${YES_NO_VI[d.yes_no.upright]} / ${YES_NO_VI[d.yes_no.reversed]}`}
              </li>
            </ul>
          )}
          <hr className="rule" />
          {d && (
            <div className="segmented tabs" role="tablist" aria-label="Nội dung lá bài">
              {TABS.map((t, i) => (
                <button key={t} role="tab" aria-selected={tab === i} onClick={() => setTab(i)}>{t}</button>
              ))}
            </div>
          )}
          <div role="tabpanel" className="tab-body">
            {(!d || tab === 0) && (
              <>
                {d && (only ? (
                  <p className="kw">{d[`keywords_${only}`].map((k) => <span key={k}>{k}</span>)}</p>
                ) : (
                  <>
                    <h3>Từ khóa xuôi</h3>
                    <p className="kw">{d.keywords_upright.map((k) => <span key={k}>{k}</span>)}</p>
                    <h3>Từ khóa ngược</h3>
                    <p className="kw">{d.keywords_reversed.map((k) => <span key={k}>{k}</span>)}</p>
                  </>
                ))}
                <h3>Ý nghĩa</h3>
                {drawn ? <p>{drawn.meaning}</p> : <Both pair={{ upright: card.upright_meaning, reversed: card.reversed_meaning }} />}
              </>
            )}
            {d && tab === 1 &&
              TOPICS.map(([key, label]) => (
                <div key={key}>
                  <h3>{label}</h3>
                  <Both pair={d[key]} only={only} />
                </div>
              ))}
            {d && tab === 2 && (
              <>
                <h3>Lời khuyên</h3>
                <p>{d.advice}</p>
                <h3>Hình ảnh trên lá</h3>
                <p>{d.imagery}</p>
              </>
            )}
          </div>
          <div className="detail-actions">
            {onToggleLike && (
              <button className={`btn-ghost ${liked ? "liked" : ""}`} onClick={onToggleLike} aria-pressed={!!liked}>
                {liked ? "♥ Đã thích" : "♡ Thích"}
              </button>
            )}
            <button className="icon-btn" onClick={() => controls.current?.spin(-7)} aria-label="Xoay sang trái">⟲</button>
            <button className="icon-btn" onClick={() => controls.current?.spin(7)} aria-label="Xoay sang phải">⟳</button>
            {(onPrev || onNext) && (
              <span className="detail-nav">
                <button className="icon-btn" onClick={onPrev} disabled={!onPrev} aria-label="Lá trước">‹</button>
                <button className="icon-btn" onClick={onNext} disabled={!onNext} aria-label="Lá sau">›</button>
              </span>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
