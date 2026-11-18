import { useState } from "react";

// card: { name, name_vi, image_url }. Ảnh lỗi thì hiện mặt bài tạm bằng tên lá.
export default function TarotCard({ card, reversed = false }) {
  const [broken, setBroken] = useState(false);
  return (
    <div className={`tarot-card ${reversed ? "reversed" : ""}`}>
      {broken || !card.image_url ? (
        <div className="card-placeholder">
          <span className="star">✦</span>
          <strong>{card.name_vi}</strong>
          <span className="small">{card.name}</span>
        </div>
      ) : (
        <img draggable={false} src={card.image_url} alt={`${card.name_vi} (${card.name})`} onError={() => setBroken(true)} />
      )}
    </div>
  );
}
