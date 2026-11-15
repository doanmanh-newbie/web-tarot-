import { useEffect, useState } from "react";
import TarotCard from "./TarotCard.jsx";

// Lật bài sau `delay` ms; bấm vào cũng lật ngay.
export default function CardFlip({ card, reversed, delay = 0 }) {
  const [flipped, setFlipped] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setFlipped(true), delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <button className={`flip ${flipped ? "flipped" : ""}`} onClick={() => setFlipped(true)} aria-label={flipped ? card.name_vi : "Lật bài"}>
      <div className="flip-inner">
        <div className="flip-back"><span>✦</span></div>
        <div className="flip-front"><TarotCard card={card} reversed={reversed} /></div>
      </div>
    </button>
  );
}
