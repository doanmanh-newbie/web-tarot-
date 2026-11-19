// Lời giải AI: phần luận giải + khung "Lời khuyên" riêng.
// Prompt backend quy định đoạn cuối luôn bắt đầu bằng "Lời khuyên:"; lời giải cũ không có đoạn này thì hiện nguyên văn.
const ADVICE = /^\s*Lời khuyên\s*:\s*/i;

export default function Interpretation({ text }) {
  const parts = text.split(/\n\s*\n/);
  const at = parts.findIndex((p) => ADVICE.test(p));
  const body = (at >= 0 ? parts.slice(0, at) : parts).join("\n\n");
  const advice = at >= 0 ? parts.slice(at).join("\n\n").replace(ADVICE, "") : null;
  return (
    <>
      {body && <div className="pre-wrap">{body}</div>}
      {advice && (
        <aside className="advice">
          <h3>✦ Lời khuyên</h3>
          <p className="pre-wrap">{advice}</p>
        </aside>
      )}
    </>
  );
}
