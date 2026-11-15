export default function QuotaBadge({ quota }) {
  if (!quota) return null;
  if (quota.unlimited) return <span className="badge">Không giới hạn lượt</span>;
  const time = new Date(quota.resets_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  return (
    <span className={`badge ${quota.remaining === 0 ? "badge-empty" : ""}`}>
      Còn {quota.remaining}/{quota.limit} lượt hôm nay · làm mới lúc {time}
    </span>
  );
}
