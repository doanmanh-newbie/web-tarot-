class DomainError(Exception):
    """Gốc của mọi lỗi nghiệp vụ. Mỗi module tự khai báo lỗi riêng, kế thừa lớp này."""


class NotAuthorized(DomainError):
    """Người dùng không có quyền với tài nguyên (vd xem reading của người khác)."""
