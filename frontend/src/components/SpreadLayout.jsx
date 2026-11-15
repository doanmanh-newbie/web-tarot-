import CardFlip from "./CardFlip.jsx";

// cards: reading.cards (đã sắp theo position_index)
export default function SpreadLayout({ cards }) {
  return (
    <div className="spread">
      {cards.map((c, i) => (
        <div className="spread-slot" key={c.position_index}>
          <div className="position-label">{c.position_label}</div>
          <CardFlip card={c.card} reversed={c.is_reversed} delay={400 + i * 500} />
          <div className="card-name">
            {c.card.name_vi} {c.is_reversed && <span className="tag">Ngược</span>}
          </div>
          <p className="small muted">{c.meaning}</p>
        </div>
      ))}
    </div>
  );
}
