from datetime import timedelta

import jwt

from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.domain.exceptions import InvalidToken
from app.shared.application.ports.clock import Clock

ALGORITHM = "HS256"


class JwtTokenService(TokenService):
    def __init__(self, secret: str, expire_minutes: int, clock: Clock) -> None:
        self._secret = secret
        self._expire = timedelta(minutes=expire_minutes)
        self._clock = clock

    def create_access_token(self, user_id: int, role: str) -> str:
        now = self._clock.now()
        payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + self._expire}
        return jwt.encode(payload, self._secret, algorithm=ALGORITHM)

    def decode(self, token: str) -> dict:
        try:
            # Chỉ cho phép đúng thuật toán đã cấu hình (chặn tấn công đổi alg/none) và bắt buộc có exp.
            return jwt.decode(
                token, self._secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken("Token không hợp lệ hoặc đã hết hạn") from exc
