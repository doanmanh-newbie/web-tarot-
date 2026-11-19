import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const Rail3D = lazy(() => import("./Rail3D.jsx"));

const DECK = 78;
const FLY_S = 0.85;
const LIFT_MS = 750; // lá nhô ra giữa khung và to dần trước khi bay xuống khay
const LIFT_H = 0.86; // chiều cao lá lúc nhô ra so với khung (khớp z/scale "lift" trong Rail3D)
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const reduceMotion = () => typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;

// Bộ bài úp dùng chung cho Bốc bài (trang chủ) và Hỏi bài:
// nút Xáo bài ngay trên bộ → cả bộ cuộn thành vòng tròn xoay → trải lại thành hàng lặp vòng.
// Chạm một lá úp (khi canPick) → lá nhô ra giữa khung, to dần → bay xuống ô trống trong khay; faces[i] có giá trị thì ô i lật ngửa.
// Mặt lá luôn do nơi gọi quyết định (ngẫu nhiên phía trình duyệt hoặc backend), lá chạm chỉ là nghi thức.
//   labels: nhãn từng ô (số ô = số lá cần rút)
//   faces:  [{ image_url, reversed, name } | null] theo ô
//   onPicked(n): đã có n lá đáp xuống khay
//   active: ô đang chọn (viền sáng); onOpenSlot(i): chạm một lá đã lật trong khay
//   aside: nội dung đặt cạnh khay (màn rộng) hoặc dưới khay (màn hẹp), vd. ý nghĩa lá đang xem
//   resetKey: đổi giá trị thì gom lá về bộ, khay trống lại
//   api.current.shuffle(ms) → Promise: xáo bài bằng code (vd. khi bấm Sẵn sàng)
export default function DeckPicker({ labels, faces = [], canPick, status, active = -1, aside, onPicked, onOpenSlot, resetKey, api }) {
  const [picks, setPicks] = useState([]); // chỉ số lá trên hàng đã rút, theo thứ tự ô
  const [landed, setLanded] = useState(0);
  const [flying, setFlying] = useState([]);
  const [shuffling, setShuffling] = useState(false);
  const [lifting, setLifting] = useState(null); // lá đang nhô ra giữa khung
  const stageRef = useRef(null);
  const rail = useRef(null);
  const slotRefs = useRef([]);
  const landedRef = useRef(0);
  const activeIdx = useRef(0); // lá đang ở giữa hàng (để rút bằng bàn phím)
  const need = labels.length;

  useEffect(() => {
    setPicks([]);
    setFlying([]);
    setLifting(null);
    setLanded(0);
    landedRef.current = 0;
  }, [resetKey]);

  const shuffle = async (ms = 1800) => {
    setShuffling(true);
    await wait(reduceMotion() ? 300 : ms);
    setShuffling(false);
    rail.current?.goTo(Math.floor(Math.random() * DECK)); // trải lại ở một chỗ ngẫu nhiên
  };
  if (api) api.current = { shuffle };

  const pick = (i) => {
    // Ô đích = ô trống đầu tiên (khay có thể đã có sẵn lá từ lần bốc dở trước)
    const slot = Math.max(picks.length, faces.filter(Boolean).length);
    if (!canPick || shuffling || lifting !== null || picks.includes(i) || slot >= need) return;
    revealTray(slot);
    setLifting(i);
    setTimeout(
      () => {
        // Lá 3D đã to ra giữa khung: thay bằng ảnh lá cùng chỗ, cùng cỡ rồi bay xuống ô trong khay
        const stage = stageRef.current?.getBoundingClientRect();
        const to = slotRefs.current[slot]?.getBoundingClientRect();
        setPicks((p) => [...p, i]);
        setLifting(null);
        if (!stage || !to) return land();
        const from = { x: stage.left + stage.width / 2, y: stage.top + stage.height / 2, scale: (stage.height * LIFT_H) / to.height };
        setFlying((f) => [...f, { id: `${resetKey}-${slot}`, from, to }]);
      },
      reduceMotion() ? 0 : LIFT_MS,
    );
  };

  // Ô đích nằm dưới mép màn hình (laptop thấp, điện thoại): cuộn lên vừa đủ để thấy cả bộ bài lẫn ô đó
  const revealTray = (slot) => {
    const sr = slotRefs.current[slot]?.getBoundingClientRect();
    const st = stageRef.current?.getBoundingClientRect();
    if (!sr || !st) return;
    const bar = document.querySelector(".tabbar");
    const bottom = bar && getComputedStyle(bar).display !== "none" ? bar.getBoundingClientRect().top : innerHeight;
    const over = sr.bottom + 16 - bottom;
    if (over > 0) scrollBy({ top: Math.min(over, st.top - 72), behavior: reduceMotion() ? "auto" : "smooth" });
  };

  const onKeyDown = (e) => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      rail.current?.goTo(activeIdx.current + (e.key === "ArrowRight" ? 1 : -1));
    } else if ((e.key === "Enter" || e.key === " ") && items[activeIdx.current]) {
      e.preventDefault();
      pick(items[activeIdx.current].id);
    }
  };

  const land = (id) => {
    if (id) setFlying((f) => f.filter((x) => x.id !== id));
    landedRef.current += 1;
    setLanded(landedRef.current);
    onPicked?.(landedRef.current);
  };

  // Lá đã rút bị bỏ khỏi hàng: key giữ nguyên nên các lá còn lại tự trượt lấp chỗ trống
  const items = Array.from({ length: DECK }, (_, i) => i)
    .filter((i) => !picks.includes(i))
    .map((i) => ({ key: `d${i}`, id: i, faceDown: true, lift: i === lifting }));

  return (
    <div className="deck">
      <div className="deck-tools">
        <button className="btn-ghost shuffle-btn" onClick={() => shuffle()} disabled={shuffling || lifting !== null}>
          ⟳ {shuffling ? "Đang xáo…" : "Xáo bài"}
        </button>
      </div>

      <div
        className={`rail-stage deck-stage ${canPick && !shuffling ? "picking" : ""}`}
        role="group"
        tabIndex={0}
        aria-label={canPick ? "Bộ bài úp: dùng phím mũi tên để lướt, Enter để rút lá ở giữa" : "Bộ bài úp, kéo ngang để lướt"}
        onKeyDown={onKeyDown}
        ref={stageRef}
      >
        <Suspense
          fallback={
            <div className="rail-skeleton" role="status" aria-label="Đang tải bộ bài">
              <div className="skeleton" />
            </div>
          }
        >
          <Rail3D
            items={items}
            api={rail}
            loop
            mode={shuffling ? "ring" : canPick ? "pick" : "rail"}
            onActive={(i) => (activeIdx.current = i)}
            onPick={(idx) => pick(items[idx].id)}
          />
        </Suspense>
        <AnimatePresence>
          {shuffling && (
            <motion.p className="spin-text" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              Đang xáo bài…
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {status && (
        <p className="deck-status" aria-live="polite">
          {status}
        </p>
      )}

      <div className={`tray-row ${aside ? "with-aside" : ""}`}>
        <ol className="tray" aria-label="Các lá đã rút">
          {labels.map((label, i) => {
            const face = faces[i];
            const filled = i < landed || !!face;
            return (
              <li key={i} className={`tray-slot ${i === active && face ? "active" : ""}`}>
                {label && <span className="slot-label">{label}</span>}
                <div className={`tray-card ${filled ? "" : "empty"}`} ref={(el) => (slotRefs.current[i] = el)}>
                  {filled && (
                    <button
                      className={`flip ${face ? "on" : ""}`}
                      onClick={() => face && onOpenSlot?.(i)}
                      aria-label={face ? `${face.name}${face.reversed ? " ngược" : ""}, xem chi tiết` : "Lá úp"}
                    >
                      <span className="flip-inner">
                        <img className="flip-face back" src="/card-back.webp" alt="" draggable={false} />
                        {face && (
                          <img
                            className={`flip-face front ${face.reversed ? "reversed" : ""}`}
                            src={face.image_url}
                            alt=""
                            draggable={false}
                          />
                        )}
                      </span>
                    </button>
                  )}
                </div>
                <span className="tray-name">
                  {face?.name}
                  {face?.reversed && <span className="tag">Ngược</span>}
                </span>
              </li>
            );
          })}
        </ol>
        {aside && <div className="tray-aside">{aside}</div>}
      </div>

      {flying.map((f) => (
        <motion.img
          key={f.id}
          src="/card-back.webp"
          alt=""
          className="fly-card"
          style={{ width: f.to.width, height: f.to.height }}
          initial={{ x: f.from.x - f.to.width / 2, y: f.from.y - f.to.height / 2, scale: f.from.scale, rotate: 0 }}
          animate={{ x: f.to.left, y: f.to.top, scale: 1, rotate: [0, -6, 0] }}
          transition={{ duration: reduceMotion() ? 0.01 : FLY_S, ease: [0.22, 1, 0.36, 1] }}
          onAnimationComplete={() => land(f.id)}
        />
      ))}
    </div>
  );
}
