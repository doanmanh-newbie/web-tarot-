from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: int, role: str) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> dict:
        """Trả payload (có `sub`). Raise InvalidToken nếu token sai chữ ký/hết hạn/hỏng."""
