import { useEffect, useState } from "react";

// Sau vài giây chưa xong thì báo máy chủ có thể đang "ngủ dậy" (Render free)
export default function LoadingState({ text = "Đang tải..." }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 6000);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="loading" role="status">
      <div className="spinner" />
      <p>{text}</p>
      {slow && <p className="muted small">Máy chủ có thể đang được đánh thức, vui lòng chờ thêm chút...</p>}
    </div>
  );
}
