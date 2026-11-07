"""Luật cho câu hỏi của người xem bài."""
from app.modules.readings.domain.exceptions import InvalidQuestion


def clean_question(text: str, max_length: int) -> str:
    cleaned = " ".join(text.split())  # bỏ khoảng trắng thừa, gộp xuống dòng
    if not cleaned:
        raise InvalidQuestion("Vui lòng nhập câu hỏi")
    if len(cleaned) > max_length:
        raise InvalidQuestion(f"Câu hỏi quá dài (tối đa {max_length} ký tự)")
    return cleaned
