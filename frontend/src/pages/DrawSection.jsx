import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { getDeck } from "../api/cards.js";
import { listSpreads } from "../api/spreads.js";
import { addLocalHistory } from "../api/localHistory.js";
import CardDetail, { YES_NO_VI } from "../components/CardDetail.jsx";
import DeckPicker from "../components/DeckPicker.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

const DRAW_KEY = "tarot_periods";
const COUNTS = [1, 3, 5];
const rand = (n) => crypto.getRandomValues(new Uint32Array(1))[0] % n;
const ymd = (d) => d.toLocaleDateString("sv"); // YYYY-MM-DD theo giờ máy người dùng
const dm = (d) => d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
function monday() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // tuần bắt đầu thứ Hai
  return d;
}

// Mỗi kỳ: khóa nhận biết kỳ hiện tại (sang kỳ mới thì lá cũ hết hiệu lực) và nhãn hiển thị
const PERIODS = {
  day: { tab: "Hôm nay", title: "Lá bài hôm nay", now: () => ymd(new Date()), label: () => `Hôm nay · ${new Date().toLocaleDateString("vi-VN")}` },
  week: {
    tab: "Tuần này",
    title: "Lá bài tuần này",
    now: () => ymd(monday()),
    label: () => {
      const m = monday();
      const s = new Date(m);
      s.setDate(m.getDate() + 6);
      return `Tuần ${dm(m)} – ${dm(s)}`;
    },
  },
  month: { tab: "Tháng này", title: "Lá bài tháng này", now: () => ymd(new Date()).slice(0, 7), label: () => `Tháng ${new Date().getMonth() + 1}/${new Date().getFullYear()}` },
  year: { tab: "Năm nay", title: "Lá bài năm nay", now: () => String(new Date().getFullYear()), label: () => `Năm ${new Date().getFullYear()}` },
};
const TOPICS = [
  ["love", "Tình cảm"],
  ["career", "Công việc"],
  ["finance", "Tài chính"],
  ["health", "Sức khỏe"],
];

// Lần bốc còn hiệu lực trong kỳ hiện tại: { [kỳ]: { key, count, cards: [{ slug, reversed }] } }
function loadDraws() {
  try {
    const all = JSON.parse(localStorage.getItem(DRAW_KEY)) ?? {};
    return Object.fromEntries(
      Object.entries(all)
        .filter(([k, v]) => PERIODS[k] && v.key === PERIODS[k].now())
        .map(([k, v]) => [k, v.cards ? v : { key: v.key, count: 1, cards: [{ slug: v.slug, reversed: v.reversed }] }]), // bản lưu cũ: 1 lá
    );
  } catch {
    return {};
  }
}
function saveDraws(draws) {
  try {
    const { yesno, ...periods } = draws; // Yes/No không giữ qua lần tải trang
    localStorage.setItem(DRAW_KEY, JSON.stringify(periods));
  } catch {
    /* trình duyệt chặn lưu: vẫn giữ trong phiên */
  }
}

// Thông tin đầy đủ của một lá đã lật, theo chiều xuôi/ngược
function CardInfo({ card, reversed, label, yesno, onOpen }) {
  const dir = reversed ? "reversed" : "upright";
  const d = card.details;
  return (
    <motion.div className="card-info" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.3 }}>
      <p className="eyebrow">{label}</p>
      {yesno && d && <p className={`yn-answer ${d.yes_no[dir]}`}>{YES_NO_VI[d.yes_no[dir]]}</p>}
      <h3 className="browse-name">
        {card.name_vi} {reversed && <span className="tag">Ngược</span>}
      </h3>
      <p className="muted small">{card.name}</p>
      {d && <p className="kw center">{d[`keywords_${dir}`].map((k) => <span key={k}>{k}</span>)}</p>}
      <p className="drawn-meaning">{reversed ? card.reversed_meaning : card.upright_meaning}</p>
      {d && (
        <div className="period-info">
          <div className="period-advice">
            <h4>Lời khuyên</h4>
            <p>{d.advice}</p>
          </div>
          {TOPICS.map(([k, t]) => (
            <div key={k}>
              <h4>{t}</h4>
              <p>{d[k][dir]}</p>
            </div>
          ))}
        </div>
      )}
      <button className="btn-ghost" onClick={onOpen}>Xem lá 3D</button>
    </motion.div>
  );
}

const PERIOD_HINT = {
  day: "Thông điệp và năng lượng nổi bật trong ngày hôm nay.",
  week: "Xu hướng chính và điều cần chú ý trong tuần này.",
  month: "Chủ đề lớn của tháng, nên tập trung vào đâu.",
  year: "Bức tranh tổng quan và bài học của cả năm.",
  yesno: "Nghĩ về một câu hỏi Có/Không rồi rút một lá.",
};
const COUNT_HINT = { 1: "Một lá: thông điệp ngắn gọn, rõ ràng.", 3: "Ba lá: quá khứ · hiện tại · tương lai.", 5: "Năm lá: phân tích kỹ một tình huống." };

// Khi chưa bốc: hướng dẫn ngắn thay cho khoảng trống cạnh khay
function DrawGuide({ mode, n }) {
  return (
    <div className="draw-guide">
      <p className="eyebrow">Cách bốc</p>
      <ol>
        <li>
          <b>Xáo bài</b>
          <span>Bấm Xáo bài phía trên bộ bài để trộn lại cả bộ.</span>
        </li>
        <li>
          <b>Chạm lá úp</b>
          <span>Lướt bộ bài, chạm lá bạn thấy cuốn hút; lá sẽ bay vào khay.</span>
        </li>
        <li>
          <b>Đọc ý nghĩa</b>
          <span>Lá lật ngửa kèm từ khóa, lời khuyên và ý nghĩa theo chủ đề.</span>
        </li>
      </ol>
      <p className="muted small">
        {PERIOD_HINT[mode]} {mode !== "yesno" && COUNT_HINT[n]}
      </p>
    </div>
  );
}

// Bốc bài nhanh: chọn kỳ (hôm nay/tuần/tháng/năm) hoặc Yes/No, chọn 1/3/5 lá, xáo bài, chạm từng lá úp
// → lá nhô ra, bay xuống khay và lật. Bốc lại bất cứ lúc nào. Mặt lá rút ngẫu nhiên trên trình duyệt (không trùng lá
// trong một lần), không tính lượt; lần bốc theo kỳ nhớ trên thiết bị, bốc xong ghi vào lịch sử trên máy.
export default function DrawSection() {
  const [mode, setMode] = useState("day");
  const [count, setCount] = useState(1);
  const [deck, setDeck] = useState(null);
  const [spreads, setSpreads] = useState([]);
  const [error, setError] = useState("");
  const [draws, setDraws] = useState(loadDraws);
  const [round, setRound] = useState(0);
  const [active, setActive] = useState(0);
  const [question, setQuestion] = useState("");
  const [detail, setDetail] = useState(null);
  const latest = useRef(); // giá trị mới nhất cho callback lá đáp xuống khay

  const load = () => {
    setError("");
    getDeck().then(setDeck).catch((err) => setError(err.message));
    listSpreads().then(setSpreads).catch(() => {}); // chỉ để lấy nhãn vị trí cho 3/5 lá
  };
  useEffect(load, []);

  const isYn = mode === "yesno";
  const draw = draws[mode];
  const n = isYn ? 1 : draw?.count ?? count;
  const periodLabel = isYn ? "Yes/No" : PERIODS[mode].label();
  const positions = spreads.find((s) => s.card_count === n)?.positions;
  const labels = n === 1 ? [periodLabel] : Array.from({ length: n }, (_, i) => positions?.[i]?.label ?? `Lá ${i + 1}`);
  const drawn = (draw?.cards ?? []).map((c) => ({ ...c, card: deck?.find((x) => x.slug === c.slug) })).filter((c) => c.card);
  const shown = drawn[Math.min(active, drawn.length - 1)];
  latest.current = { mode, isYn, deck, draws, question, n, labels, periodLabel };

  // Một lá vừa đáp xuống khay: lúc này mới rút mặt lá ngẫu nhiên (không trùng lá đã ra) rồi lật
  const onPicked = () => {
    const { mode, isYn, deck, draws, question, n, labels, periodLabel } = latest.current;
    if (!deck) return;
    const prev = draws[mode]?.cards ?? [];
    const pool = deck.filter((c) => !prev.some((p) => p.slug === c.slug));
    const cards = [...prev, { slug: pool[rand(pool.length)].slug, reversed: rand(2) === 1 }];
    setTimeout(() => {
      const next = { ...draws, [mode]: { key: isYn ? "" : PERIODS[mode].now(), count: n, cards } };
      setDraws(next);
      setActive(cards.length - 1);
      saveDraws(next);
      if (cards.length === n)
        addLocalHistory({
          kind: mode,
          period: isYn ? undefined : periodLabel,
          question: isYn ? question.trim() : undefined,
          cards: cards.map((c, i) => ({ ...c, label: n > 1 ? labels[i] : undefined })),
        });
    }, 250);
  };

  // Xóa lần bốc của mục hiện tại, gom lá về bộ để bốc lại (có thể đổi số lá)
  const again = (nextCount = count) => {
    const { [mode]: _, ...rest } = draws;
    setDraws(rest);
    saveDraws(rest);
    setCount(nextCount);
    setActive(0);
    setRound((r) => r + 1);
  };
  const chooseCount = (c) => (draw ? again(c) : setCount(c));
  const open = () => setDetail({ card: shown.card, is_reversed: shown.reversed, position_label: labels[active] });

  return (
    <section id="boc-bai" className="section draw">
      <header className="browse-head">
        <p className="eyebrow">Rút bài cho bạn</p>
        <h2 className="section-title">{isYn ? "Có hay Không?" : PERIODS[mode].title}</h2>
        <div className="segmented filters" role="tablist" aria-label="Kiểu bốc bài">
          {Object.entries(PERIODS).map(([k, p]) => (
            <button key={k} role="tab" aria-selected={mode === k} onClick={() => (setMode(k), setActive(0))}>
              {p.tab}
              {draws[k]?.cards.length === draws[k]?.count && " ✓"}
            </button>
          ))}
          <button role="tab" aria-selected={isYn} onClick={() => (setMode("yesno"), setActive(0))}>Yes/No</button>
        </div>
      </header>

      <div className="draw-controls">
        {isYn ? (
          <div className="ask-row yn-ask">
            <input
              maxLength={200}
              placeholder="Câu hỏi Có/Không (không bắt buộc)"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              aria-label="Câu hỏi Có hoặc Không"
            />
          </div>
        ) : (
          <div className="segmented" role="radiogroup" aria-label="Số lá">
            {COUNTS.map((c) => (
              <button key={c} role="radio" aria-checked={n === c} aria-selected={n === c} onClick={() => chooseCount(c)}>
                {c} lá
              </button>
            ))}
          </div>
        )}
        {draw && (
          <button className="btn-ghost redraw" onClick={() => again()}>
            ↺ Bốc lại
          </button>
        )}
      </div>

      <ErrorMessage message={error} onRetry={load} />

      <DeckPicker
        labels={labels}
        faces={labels.map((_, i) => drawn[i] && { image_url: drawn[i].card.image_url, reversed: drawn[i].reversed, name: drawn[i].card.name_vi })}
        canPick={!!deck && drawn.length < n}
        status={drawn.length < n ? (n === 1 ? "Nghĩ về điều bạn muốn hỏi rồi chạm một lá úp" : `Chạm chọn ${n} lá · đã chọn ${drawn.length}/${n}`) : null}
        active={active}
        resetKey={`${mode}-${round}`}
        onPicked={onPicked}
        onOpenSlot={setActive}
        aside={
          shown ? (
            <CardInfo
              key={`${mode}-${shown.slug}`}
              card={shown.card}
              reversed={shown.reversed}
              label={labels[Math.min(active, drawn.length - 1)] + (drawn.length > 1 ? " · chạm lá khác trong khay để xem" : "")}
              yesno={isYn}
              onOpen={open}
            />
          ) : (
            <DrawGuide mode={mode} n={n} />
          )
        }
      />

      <div className="ask-cta panel">
        <div>
          <h3>Có câu hỏi cụ thể?</h3>
          <p className="muted small">Chọn kiểu trải bài, đặt câu hỏi và nhận lời giải chi tiết từ AI.</p>
        </div>
        <Link className="btn" to="/hoi-bai">✦ Hỏi Ngay</Link>
      </div>

      <AnimatePresence>
        {detail && (
          <CardDetail
            card={detail.card}
            drawn={{
              is_reversed: detail.is_reversed,
              meaning: detail.is_reversed ? detail.card.reversed_meaning : detail.card.upright_meaning,
              position_label: detail.position_label,
            }}
            onClose={() => setDetail(null)}
          />
        )}
      </AnimatePresence>
    </section>
  );
}
