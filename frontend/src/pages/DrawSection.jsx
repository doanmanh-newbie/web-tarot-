import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { listSpreads } from "../api/spreads.js";
import { getQuota } from "../api/quota.js";
import { createReading } from "../api/readings.js";
import QuotaBadge from "../components/QuotaBadge.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import CardDetail from "../components/CardDetail.jsx";
import { RING } from "../components/three/constants.js";

const Rail3D = lazy(() => import("../components/Rail3D.jsx"));

const MIN_SPIN_MS = 2600; // vòng tròn quay đủ lâu cho có cảm giác, kể cả khi API trả nhanh
const FLY_MS = 900; // chờ các lá bay ra hàng trước rồi mới lật
const FLIP_EVERY_MS = 750;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// Chọn ngẫu nhiên n vị trí trên vòng tròn để rút lá ra (chỉ là hiệu ứng; lá thật do backend bốc)
function sampleSlots(n) {
  const slots = Array.from({ length: RING }, (_, i) => i);
  for (let i = slots.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [slots[i], slots[j]] = [slots[j], slots[i]];
  }
  return slots.slice(0, n);
}

// Bốc bài trên chính hàng lá 3D của trang lướt bài:
// lướt bộ bài úp → bấm bốc → cả bộ cuộn thành vòng tròn và xoay → vài lá ngẫu nhiên bay ra rồi lật ngửa.
export default function DrawSection() {
  const navigate = useNavigate();
  const [spreads, setSpreads] = useState(null);
  const [quota, setQuota] = useState(null);
  const [selected, setSelected] = useState(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [phase, setPhase] = useState("browse"); // browse | spin | reveal
  const [reading, setReading] = useState(null);
  const [chosen, setChosen] = useState([]);
  const [revealed, setRevealed] = useState(0);
  const [detail, setDetail] = useState(null);
  const rail = useRef(null);

  const load = () => {
    setError("");
    Promise.all([listSpreads(), getQuota()])
      .then(([s, q]) => {
        setSpreads(s);
        setQuota(q);
        setSelected((cur) => cur ?? s[0]?.id ?? null);
      })
      .catch((err) => setError(err.message));
  };
  useEffect(load, []);

  // Lật từng lá sau khi chúng bay ra hàng phía trước
  useEffect(() => {
    if (phase !== "reveal" || !reading) return;
    let t;
    const start = setTimeout(() => {
      setRevealed(1);
      t = setInterval(() => setRevealed((n) => Math.min(n + 1, reading.cards.length)), FLIP_EVERY_MS);
    }, FLY_MS);
    return () => {
      clearTimeout(start);
      clearInterval(t);
    };
  }, [phase, reading]);

  const draw = async (e) => {
    e.preventDefault();
    if (!question.trim()) return setError("Hãy nhập câu hỏi của bạn.");
    setError("");
    setRevealed(0);
    setPhase("spin");
    try {
      const [r] = await Promise.all([createReading(selected, question.trim()), wait(MIN_SPIN_MS)]);
      setReading(r);
      setChosen(sampleSlots(r.cards.length));
      setPhase("reveal");
    } catch (err) {
      setError(err.message);
      getQuota().then(setQuota).catch(() => {});
      setPhase("browse");
    }
  };

  const again = () => {
    setReading(null);
    setChosen([]);
    setRevealed(0);
    setPhase("browse");
    getQuota().then(setQuota).catch(() => {});
  };

  if (!spreads)
    return (
      <section id="boc-bai" className="section draw">
        {error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />}
      </section>
    );

  const outOfQuota = quota && !quota.unlimited && quota.remaining === 0;
  const done = reading && revealed >= reading.cards.length;
  // Bộ 78 lá úp; lá được rút sẽ mang mặt của lá backend đã bốc và lật lên khi tới lượt
  const items = Array.from({ length: 78 }, (_, i) => {
    const slot = chosen.indexOf(i);
    const c = slot >= 0 ? reading?.cards[slot] : null;
    return c
      ? { key: `d${i}`, image_url: c.card.image_url, reversed: c.is_reversed, faceDown: slot >= revealed }
      : { key: `d${i}`, faceDown: true };
  });
  const last = reading?.cards[Math.max(0, revealed - 1)];

  return (
    <section id="boc-bai" className="section draw">
      <header className="browse-head">
        <p className="eyebrow">{phase === "browse" ? "Tập trung vào câu hỏi" : reading?.spread.name ?? "Đang xào bài"}</p>
        <h2 className="section-title">{phase === "reveal" ? `“${reading.question}”` : "Bốc bài"}</h2>
      </header>

      <div className={`rail-stage draw-stage ${phase}`}>
        <Suspense fallback={null}>
          <Rail3D items={items} api={rail} mode={phase === "browse" ? "rail" : phase === "spin" ? "ring" : "reveal"} chosen={chosen} onOpen={(slot) => slot < revealed && setDetail(reading.cards[slot])} />
        </Suspense>
        <AnimatePresence>
          {phase === "spin" && (
            <motion.p className="spin-text" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              Đang xào bài…
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait">
        {phase === "browse" && (
          <motion.form key="ask" className="ask" onSubmit={draw} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}>
            <div className="chips" role="radiogroup" aria-label="Kiểu trải bài">
              {spreads.map((s) => (
                <button type="button" key={s.id} role="radio" aria-checked={selected === s.id} className="chip" onClick={() => setSelected(s.id)}>
                  {s.name} <span>{s.card_count} lá</span>
                </button>
              ))}
            </div>
            <div className="ask-row">
              <input
                maxLength={300}
                placeholder="Bạn muốn hỏi điều gì?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                aria-label="Câu hỏi"
              />
              <button className="btn" disabled={!selected || outOfQuota}>✦ Xoay & bốc</button>
            </div>
            <div className="ask-foot">
              <span className="muted small">Kéo để lướt bộ bài úp</span>
              <QuotaBadge quota={quota} />
            </div>
            <ErrorMessage message={error} />
            {outOfQuota && <p className="muted small">Bạn đã dùng hết lượt hôm nay. Hãy quay lại sau giờ làm mới.</p>}
          </motion.form>
        )}

        {phase === "reveal" && (
          <motion.div key="result" className="draw-meta" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <ol className="slots">
              {reading.cards.map((c, i) => (
                <li key={c.position_index}>
                  <button className={`slot ${i < revealed ? "on" : ""}`} disabled={i >= revealed} onClick={() => setDetail(c)}>
                    <span className="slot-label">{c.position_label}</span>
                    <span className="slot-name">{i < revealed ? c.card.name_vi : "···"}</span>
                    {i < revealed && c.is_reversed && <span className="tag">Ngược</span>}
                  </button>
                </li>
              ))}
            </ol>
            {revealed > 0 && last && <p className="small drawn-meaning">{last.meaning}</p>}
            {done && (
              <motion.div className="row-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <button className="btn btn-lg" onClick={() => navigate(`/readings/${reading.id}`, { state: { reading } })}>Xem lời giải</button>
                <button className="btn-ghost" onClick={again}>Bốc lại</button>
              </motion.div>
            )}
            <p className="hint">Chạm lá để xem chi tiết 3D</p>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {detail && (
          <CardDetail
            card={detail.card}
            drawn={{ is_reversed: detail.is_reversed, meaning: detail.meaning, position_label: detail.position_label }}
            onClose={() => setDetail(null)}
          />
        )}
      </AnimatePresence>
    </section>
  );
}
