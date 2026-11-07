from app.shared.domain.exceptions import DomainError


class EmailAlreadyUsed(DomainError):
    """Email đã được đăng ký."""


class InvalidCredentials(DomainError):
    """Sai email hoặc mật khẩu (cố ý không nói rõ cái nào sai)."""


class InvalidToken(DomainError):
    """Token thiếu, sai chữ ký, hết hạn, hoặc user trong token không còn tồn tại."""


class WeakPassword(DomainError):
    """Mật khẩu không đạt chính sách."""
