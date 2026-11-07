"""Luật cho nội dung ý nghĩa lá bài (admin sửa)."""
from app.modules.cards.domain.exceptions import InvalidCardMeaning

MAX_LENGTH = 1000


def clean_meaning(text: str, label: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise InvalidCardMeaning(f"{label} không được để trống")
    if len(cleaned) > MAX_LENGTH:
        raise InvalidCardMeaning(f"{label} quá dài (tối đa {MAX_LENGTH} ký tự)")
    return cleaned
