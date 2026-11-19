import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { listSpreads } from "../api/spreads.js";
import { getQuota } from "../api/quota.js";
import { createReading, reinterpret } from "../api/readings.js";
import QuotaBadge from "../components/QuotaBadge.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import CardDetail from "../components/CardDetail.jsx";
import DeckPicker from "../components/DeckPicker.jsx";
import Interpretation from "../components/Interpretation.jsx";
import AccuracyRating from "../components/AccuracyRating.jsx";

const SHUFFLE_MS = 2400; // vòng tròn xáo bài quay đủ lâu cho có cảm giác
const FLIP_EVERY_MS = 650;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const TOPICS = ["Chung", "Tình cảm", "Công việc", "Tài chính", "Sức khỏe", "Học tập"];
// Người hỏi là ai: gửi kèm câu hỏi để lời khuyên sát hoàn cảnh thực tế ("" = không nói rõ)
const PERSONAS = [
  ["", "Không nói rõ"],
  ["học sinh", "Học sinh"],
  ["sinh viên", "Sinh viên"],
  ["người mới đi làm", "Mới đi làm"],
  ["dân văn phòng", "Dân văn phòng"],
  ["người lao động tự do", "Lao động tự do"],
  ["freelancer", "Freelancer"],
  ["chủ quán, người kinh doanh nhỏ", "Chủ quán / buôn bán"],
  ["chủ doanh nghiệp", "Chủ doanh nghiệp"],
  ["người nội trợ", "Nội trợ"],
  ["phụ huynh", "Phụ huynh"],
  ["người nghỉ hưu", "Nghỉ hưu"],
];
const PERSONA_KEY = "tarot_persona";
const loadPersona = () => {
  try {
    return localStorage.getItem(PERSONA_KEY) ?? "";
  } catch {
    return "";
  }
};
// Ghép đối tượng + chủ đề vào câu hỏi; vẫn giữ giới hạn 300 ký tự của backend
const composeQuestion = (persona, topic, question) =>
  [persona && `Tôi là ${persona}.`, topic === TOPICS[0] ? question : `Chủ đề ${topic.toLowerCase()}: ${question}`]
    .filter(Boolean)
    .join(" ")
    .slice(0, 300);
const fade = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -12 } };

// Hỏi bài với AI (trang riêng): đặt câu hỏi → Sẵn sàng → xáo bài → tự chạm chọn đủ số lá, từng lá bay xuống khay
// → backend bốc mặt lá thật và giải → các lá trong khay lật lần lượt → xem lời giải.
// Chỉ gọi backend khi đã chọn đủ lá, nên bỏ ngang giữa chừng không mất lượt.
export default function AskPage() {
  const navigate = useNavigate();
  const [spreads, setSpreads] = useState(null);
  const [quota, setQuota] = useState(null);
  const [selected, setSelected] = useState(null);
  const [question, setQuestion] = useState("");
  const [topic, setTopic] = useState(TOPICS[0]);
  const [persona, setPersona] = useState(loadPersona);
  const choosePersona = (p) => {
    setPersona(p);
    try {
      localStorage.setItem(PERSONA_KEY, p); // nhớ cho lần hỏi sau trên thiết bị này
    } catch {
      /* trình duyệt chặn lưu: bỏ qua */
    }
  };
  const [error, setError] = useState("");
  const [phase, setPhase] = useState("form"); // form | spin | pick | reading | failed | reveal
  const [picked, setPicked] = useState(0);
  const [reading, setReading] = useState(null);
  const [revealed, setRevealed] = useState(0);
  const [round, setRound] = useState(0);
  const [detail, setDetail] = useState(null);
  const [interp, setInterp] = useState("idle"); // idle | loading | failed — lời giải AI, tải SAU khi đã lật hết lá
  const deck = useRef(null);
  const latest = useRef();

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

  // Lật từng lá trong khay ngay khi backend trả lá (chưa chờ AI)
  const readingId = reading?.id;
  const cardCount = reading?.cards.length ?? 0;
  useEffect(() => {
    if (phase !== "reveal" || !readingId) return;
    const t = setInterval(() => setRevealed((n) => Math.min(n + 1, cardCount)), FLIP_EVERY_MS);
    setRevealed(1);
    return () => clearInterval(t);
  }, [phase, readingId, cardCount]);

  // Lật hết lá rồi mới gọi AI luận giải; người dùng xem lá trong lúc chờ
  const allShown = phase === "reveal" && reading && revealed >= cardCount;
  const needsAi = allShown && reading.ai_status !== "done";
  const interpretNow = () => {
    setInterp("loading");
    reinterpret(readingId)
      .then((r) => {
        setReading(r);
        setInterp(r.ai_status === "done" ? "idle" : "failed");
      })
      .catch(() => setInterp("failed"));
  };
  useEffect(() => {
    if (needsAi && interp === "idle") interpretNow();
  }, [needsAi]);

  if (!spreads)
    return <div className="draw ask-page">{error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />}</div>;

  const spread = spreads.find((s) => s.id === selected);
  const need = spread?.card_count ?? 0;
  const outOfQuota = quota && !quota.unlimited && quota.remaining === 0;
  const done = reading && revealed >= reading.cards.length;
  latest.current = { need, selected, topic, question, persona };

  const ready = async (e) => {
    e.preventDefault();
    if (!question.trim()) return setError("Hãy nhập câu hỏi của bạn.");
    setError("");
    setPhase("spin");
    await deck.current.shuffle(SHUFFLE_MS);
    setPhase("pick");
  };

  // Một lá vừa đáp xuống khay; đủ lá thì mới gọi backend bốc và giải
  const onPicked = (n) => {
    setPicked(n);
    if (n >= latest.current.need) request();
  };

  // Gọi backend bốc lá (chưa giải). Lỗi thì giữ nguyên các lá đã chọn để thử lại, không bắt xáo/chọn lại từ đầu
  const request = async () => {
    const { selected, topic, question, persona } = latest.current;
    setError("");
    setPhase("reading");
    try {
      // Đối tượng + chủ đề gửi kèm trong câu hỏi để AI giải đúng hoàn cảnh và khía cạnh
      const q = composeQuestion(persona, topic, question.trim());
      const [r] = await Promise.all([createReading(selected, q, false), wait(500)]);
      setReading(r);
      setPhase("reveal");
    } catch (err) {
      setError(err.message);
      getQuota().then(setQuota).catch(() => {});
      setPhase("failed");
    }
  };

  const reset = () => {
    setReading(null);
    setRevealed(0);
    setPicked(0);
    setInterp("idle");
    setRound((n) => n + 1);
    setPhase("form");
    getQuota().then(setQuota).catch(() => {});
  };

  const faces = (spread?.positions ?? []).map((_, i) => {
    const c = reading?.cards[i];
    return c && i < revealed ? { image_url: c.card.image_url, reversed: c.is_reversed, name: c.card.name_vi } : null;
  });
  const status =
    phase === "form"
      ? null
      : phase === "spin"
        ? " "
        : phase === "pick"
          ? `Chạm chọn ${need} lá · đã chọn ${picked}/${need}`
          : phase === "reading"
            ? "Đang lật các lá bạn chọn…"
            : null;
  const last = reading?.cards[Math.max(0, revealed - 1)];

  return (
    <div className="draw ask-page">
      <header className="browse-head">
        <p className="eyebrow">{phase === "form" ? "Hỏi bài với AI" : spread?.name}</p>
        <h1 className="section-title">{phase === "form" ? "Bạn muốn hỏi điều gì?" : `“${question.trim()}”`}</h1>
      </header>

      <AnimatePresence mode="wait">
        {phase === "form" ? (
          <motion.form key="ask" className="ask" onSubmit={ready} {...fade}>
            <div className="chips" role="radiogroup" aria-label="Kiểu trải bài">
              {spreads.map((s) => (
                <button type="button" key={s.id} role="radio" aria-checked={selected === s.id} className="chip" onClick={() => setSelected(s.id)}>
                  {s.name} <span>{s.card_count} lá</span>
                </button>
              ))}
            </div>
            <div className="chips topics" role="radiogroup" aria-label="Chủ đề">
              {TOPICS.map((t) => (
                <button type="button" key={t} role="radio" aria-checked={topic === t} className="chip" onClick={() => setTopic(t)}>
                  {t}
                </button>
              ))}
            </div>
            <div className="persona">
              <span className="persona-label">Bạn là</span>
              <div className="chips persona-chips" role="radiogroup" aria-label="Bạn là">
                {PERSONAS.map(([v, label]) => (
                  <button type="button" key={label} role="radio" aria-checked={persona === v} className="chip" onClick={() => choosePersona(v)}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div className="ask-row">
              <input maxLength={300} placeholder="Bạn muốn hỏi điều gì?" value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Câu hỏi" />
              {persona && (
                <span className="tag ask-persona" title="Lựa chọn được nhớ từ lần trước, đổi ở dòng Bạn là phía trên">
                  Bạn là {PERSONAS.find(([v]) => v === persona)?.[1]}
                </span>
              )}
              <button className="btn" disabled={!selected || outOfQuota}>✦ Sẵn sàng</button>
            </div>
            <div className="ask-foot">
              <span className="muted small">{spread?.description}</span>
              <QuotaBadge quota={quota} />
            </div>
            <ErrorMessage message={error} />
            {outOfQuota && <p className="muted small">Bạn đã dùng hết lượt hôm nay. Hãy quay lại sau giờ làm mới.</p>}
          </motion.form>
        ) : (
          <motion.div key="bar" className="row-center ask-bar" {...fade}>
            {persona && <span className="tag">{PERSONAS.find(([v]) => v === persona)?.[1]}</span>}
            {topic !== TOPICS[0] && <span className="tag">{topic}</span>}
            {(phase === "pick" || done) && (
              <button className="btn-ghost" onClick={reset}>
                {done ? "Hỏi câu khác" : "Đổi câu hỏi"}
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <DeckPicker
        api={deck}
        labels={(spread?.positions ?? []).map((p) => p.label)}
        faces={faces}
        canPick={phase === "pick"}
        status={status}
        resetKey={round}
        onPicked={onPicked}
        onOpenSlot={(i) => setDetail(reading.cards[i])}
      />

      {phase === "failed" && (
        <motion.div className="draw-meta" {...fade}>
          <ErrorMessage message={error} />
          <div className="row-center">
            <button className="btn" onClick={request} disabled={outOfQuota}>Thử lại</button>
            <button className="btn-ghost" onClick={reset}>Hỏi câu khác</button>
          </div>
        </motion.div>
      )}

      {phase === "reveal" && (
        <motion.div className="draw-meta" {...fade}>
          {!done && last && revealed > 0 && (
            <p className="drawn-meaning">
              <b>{last.position_label}:</b> {last.meaning}
            </p>
          )}
          {done && (
            <ul className="ask-meanings">
              {reading.cards.map((c) => (
                <li key={c.position_index}>
                  <span className="slot-label">{c.position_label}</span>
                  <b>
                    {c.card.name_vi}
                    {c.is_reversed && " (ngược)"}
                  </b>
                  <span className="muted small">{c.meaning}</span>
                </li>
              ))}
            </ul>
          )}
          {done && (
            <motion.section className="panel interpretation ask-interp" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <h2>Lời diễn giải</h2>
              {reading.ai_status === "done" ? (
                <>
                  <Interpretation text={reading.ai_interpretation} />
                  <AccuracyRating reading={reading} onRated={setReading} />
                  <div className="row-center">
                    <button className="btn-ghost" onClick={() => navigate(`/readings/${reading.id}`, { state: { reading } })}>Mở trang kết quả</button>
                  </div>
                </>
              ) : interp === "failed" ? (
                <div>
                  <p className="muted">AI đang bận hoặc gặp lỗi. Giải lại không tốn thêm lượt.</p>
                  <button className="btn" onClick={interpretNow}>Giải lại</button>
                </div>
              ) : (
                <div className="interp-loading" role="status">
                  <p className="muted">AI đang luận giải các lá bạn vừa rút…</p>
                  <div className="skeleton line" />
                  <div className="skeleton line" />
                  <div className="skeleton line short" />
                </div>
              )}
            </motion.section>
          )}
        </motion.div>
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
