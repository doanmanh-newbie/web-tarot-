from app.shared.domain.exceptions import DomainError


class ReadingNotFound(DomainError):
    """Không có reading này, hoặc reading thuộc người khác (cố ý không phân biệt để không lộ sự tồn tại)."""


class InterpretationFailed(DomainError):
    """Dịch vụ AI lỗi, hết thời gian, bị chặn, hoặc trả nội dung rỗng."""


class InvalidQuestion(DomainError):
    """Câu hỏi rỗng hoặc quá dài."""


class InvalidAccuracy(DomainError):
    """Điểm đánh giá ngoài 0-100, hoặc reading chưa có lời giải để đánh giá."""


class DeckNotReady(DomainError):
    """Bộ bài chưa được nạp (chưa chạy seed) hoặc không đủ lá cho kiểu trải bài."""
