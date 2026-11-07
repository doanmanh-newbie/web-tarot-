from app.modules.readings.application.ports.ai_interpreter import AIInterpreter, CardForPrompt


class OfflineInterpreter(AIInterpreter):
    """Diễn giải mẫu ghép từ ý nghĩa gốc, không gọi mạng. Dùng khi AI_PROVIDER=offline:
    dev frontend khi chưa có API key, chạy demo khi mất mạng, hoặc test không tốn quota Gemini."""

    def interpret(self, question: str, spread_name: str, cards: list[CardForPrompt]) -> str:
        parts = [f"(Bản diễn giải mẫu, không dùng AI) Với câu hỏi của bạn, kiểu trải bài \"{spread_name}\" cho thấy:"]
        for card in cards:
            orientation = "ngược" if card.is_reversed else "xuôi"
            parts.append(f"- {card.position_label}: {card.name} ({orientation}). {card.base_meaning}")
        parts.append("Hãy xem đây là gợi ý để suy ngẫm, không phải lời tiên đoán chắc chắn.")
        return "\n".join(parts)
