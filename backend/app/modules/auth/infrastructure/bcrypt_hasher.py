import bcrypt

from app.modules.auth.application.ports.password_hasher import PasswordHasher


class BcryptHasher(PasswordHasher):
    def __init__(self, rounds: int = 12) -> None:
        # rounds càng cao càng chậm và càng khó brute-force. Test dùng rounds thấp cho nhanh.
        self._rounds = rounds

    def hash(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=self._rounds)).decode("ascii")

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
        except ValueError:
            # hash hỏng hoặc mật khẩu vượt giới hạn của bcrypt
            return False
