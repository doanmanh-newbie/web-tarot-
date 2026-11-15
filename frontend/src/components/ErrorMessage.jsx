export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="alert" role="alert">
      <span>{message}</span>
      {onRetry && <button className="btn-ghost" onClick={onRetry}>Thử lại</button>}
    </div>
  );
}
