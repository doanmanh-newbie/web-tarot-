import { lazy, Suspense, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { listSpreads } from "../api/spreads.js";
import BrowseSection from "./BrowseSection.jsx";
import DrawSection from "./DrawSection.jsx";

const CardModel3D = lazy(() => import("../components/CardModel3D.jsx"));

// Lá trưng bày ở phần mở đầu (chỉ để trang trí)
const HERO_CARD = { image_url: "/cards/the-star.webp", name: "The Star", name_vi: "Ngôi Sao" };

const fadeUp = {
  initial: { opacity: 0, y: 40 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
};

const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

function Hero() {
  return (
    <section id="top" className="hero">
      <motion.div className="hero-copy" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}>
        <p className="eyebrow">Rider–Waite · 78 lá · 3D</p>
        <h1 className="hero-title">
          Lắng nghe <em>lá bài</em>
          <br />
          kể chuyện của bạn
        </h1>
        <p className="hero-sub">Lướt bộ bài cổ điển như lướt bộ sưu tập, rồi đặt câu hỏi và để vòng bài chọn cho bạn vài lá.</p>
        <div className="hero-cta">
          <button className="btn btn-lg" onClick={() => scrollTo("boc-bai")}>✦ Bốc bài ngay</button>
          <button className="btn-ghost" onClick={() => scrollTo("bo-bai")}>Lướt bộ bài</button>
        </div>
      </motion.div>
      <motion.div className="hero-card" initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.1, delay: 0.2 }}>
        <Suspense fallback={null}>
          <CardModel3D card={HERO_CARD} className="hero-canvas" />
        </Suspense>
      </motion.div>
      <button className="scroll-cue" onClick={() => scrollTo("bo-bai")} aria-label="Cuộn xuống">
        <span />
      </button>
    </section>
  );
}

function SpreadsGuide() {
  const [spreads, setSpreads] = useState([]);
  useEffect(() => {
    listSpreads().then(setSpreads).catch(() => {});
  }, []);
  if (!spreads.length) return null;
  return (
    <section id="kieu-trai" className="section guide">
      <motion.header className="browse-head" {...fadeUp}>
        <p className="eyebrow">Ba cách đặt câu hỏi</p>
        <h2 className="section-title">Kiểu trải bài</h2>
      </motion.header>
      <div className="guide-grid">
        {spreads.map((s, i) => (
          <motion.article key={s.id} className="guide-card" {...fadeUp} transition={{ ...fadeUp.transition, delay: i * 0.12 }}>
            <p className="guide-count">{s.card_count}</p>
            <h3>{s.name}</h3>
            <p className="muted small">{s.description}</p>
            <ol className="guide-positions">
              {s.positions.map((p) => (
                <li key={p.index}>{p.label}</li>
              ))}
            </ol>
          </motion.article>
        ))}
      </div>
      <motion.div className="row-center" {...fadeUp}>
        <button className="btn" onClick={() => scrollTo("boc-bai")}>✦ Thử bốc một lượt</button>
      </motion.div>
    </section>
  );
}

// Trang chủ dạng một trang dài: mở đầu → bộ bài → bốc bài → kiểu trải bài → chân trang
export default function HomePage() {
  const { hash } = useLocation();

  // Vào từ thanh điều hướng (/#boc-bai...) thì cuộn tới đúng phần
  useEffect(() => {
    if (!hash) return;
    const t = setTimeout(() => scrollTo(hash.slice(1)), 50);
    return () => clearTimeout(t);
  }, [hash]);

  return (
    <div className="landing">
      <Hero />
      {/* Không bọc motion: transform ở tổ tiên làm lớp chi tiết position:fixed bị lệch */}
      <BrowseSection />
      <DrawSection />
      <SpreadsGuide />
      <footer className="site-footer">
        <p className="brand-mark">✦ Tarot</p>
        <p className="muted small">Nội dung chỉ mang tính giải trí và tham khảo, không thay thế lời khuyên của chuyên gia.</p>
        <p className="muted small">Hình lá bài: bộ Rider–Waite–Smith (1909), phạm vi công cộng.</p>
      </footer>
    </div>
  );
}
