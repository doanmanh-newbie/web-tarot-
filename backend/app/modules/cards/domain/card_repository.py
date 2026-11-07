from abc import ABC, abstractmethod

from app.modules.cards.domain.card import Card


class CardRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Card]:
        """Toàn bộ bộ bài, sắp theo id."""

    @abstractmethod
    def list_ids(self) -> list[int]:
        """Chỉ id của toàn bộ bộ bài (sắp tăng dần). Dùng để bốc ngẫu nhiên."""

    @abstractmethod
    def get_by_id(self, card_id: int) -> Card | None: ...

    @abstractmethod
    def get_by_ids(self, card_ids: list[int]) -> list[Card]:
        """Trả các lá tồn tại, ĐÚNG thứ tự của `card_ids`; id không tồn tại bị bỏ qua.
        Module readings dùng để lấy ý nghĩa gốc của các lá vừa bốc."""

    @abstractmethod
    def update_meaning(self, card_id: int, upright: str, reversed_: str) -> Card:
        """Raise CardNotFound nếu không có lá này."""
