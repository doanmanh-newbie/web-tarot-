"""Chính sách mật khẩu (luật thuần, dễ test).

bcrypt chỉ xử lý tối đa 72 byte đầu, nên phải chặn trên theo BYTE (không phải ký tự),
nếu không hai mật khẩu khác nhau ở phần đuôi sẽ bị coi là một.
"""
from app.modules.auth.domain.exceptions import WeakPassword

MIN_LENGTH = 8
MAX_BYTES = 72


def validate_password(plain: str) -> None:
    if len(plain) < MIN_LENGTH:
        raise WeakPassword(f"Mật khẩu phải có ít nhất {MIN_LENGTH} ký tự")
    if len(plain.encode("utf-8")) > MAX_BYTES:
        raise WeakPassword(f"Mật khẩu quá dài (tối đa {MAX_BYTES} byte)")
    if plain.strip() == "":
        raise WeakPassword("Mật khẩu không được chỉ gồm khoảng trắng")
