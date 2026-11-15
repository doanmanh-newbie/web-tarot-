import { useEffect, useState } from "react";
import { listCards, updateCard } from "../api/admin.js";
import TarotCard from "../components/TarotCard.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";

function CardEditor({ card, onSaved }) {
  const [up, setUp] = useState(card.upright_meaning);
  const [rev, setRev] = useState(card.reversed_meaning);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const save = async (e) => {
    e.preventDefault();
    setError("");
    setMsg("");
    setBusy(true);
    try {
      onSaved(await updateCard(card.id, up.trim(), rev.trim()));
      setMsg("Đã lưu.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="panel admin-editor" onSubmit={save}>
      <div className="admin-card-preview"><TarotCard card={card} /></div>
      <div className="grow">
        <h2>{card.name_vi} <span className="muted small">({card.name})</span></h2>
        <label>Ý nghĩa xuôi<textarea rows={4} maxLength={1000} value={up} onChange={(e) => setUp(e.target.value)} required /></label>
        <label>Ý nghĩa ngược<textarea rows={4} maxLength={1000} value={rev} onChange={(e) => setRev(e.target.value)} required /></label>
        <ErrorMessage message={error} />
        {msg && <p className="success">{msg}</p>}
        <button className="btn" disabled={busy}>{busy ? "Đang lưu..." : "Lưu"}</button>
      </div>
    </form>
  );
}

export default function AdminCardsPage() {
  const [cards, setCards] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    listCards().then(setCards).catch((err) => setError(err.message));
  };
  useEffect(load, []);

  if (!cards) return error ? <ErrorMessage message={error} onRetry={load} /> : <LoadingState />;

  const q = filter.toLowerCase();
  const shown = cards.filter((c) => `${c.name} ${c.name_vi}`.toLowerCase().includes(q));
  const selected = cards.find((c) => c.id === selectedId);

  return (
    <div>
      <h1>Quản lý ý nghĩa lá bài</h1>
      <div className="admin-layout">
        <aside className="panel admin-list">
          <input placeholder="Tìm lá bài..." value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Tìm lá bài" />
          <ul>
            {shown.map((c) => (
              <li key={c.id}>
                <button className={c.id === selectedId ? "active" : ""} onClick={() => setSelectedId(c.id)}>
                  {c.name_vi} <span className="muted small">{c.name}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
        {selected ? (
          <CardEditor
            key={selected.id}
            card={selected}
            onSaved={(u) => setCards((cur) => cur.map((c) => (c.id === u.id ? u : c)))}
          />
        ) : (
          <p className="muted">Chọn một lá bài để sửa.</p>
        )}
      </div>
    </div>
  );
}
