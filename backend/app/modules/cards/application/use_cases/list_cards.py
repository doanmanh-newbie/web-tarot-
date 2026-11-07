from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository


class ListCards:
    """Admin xem toàn bộ bộ bài."""

    def __init__(self, cards: CardRepository) -> None:
        self._cards = cards

    def execute(self) -> list[Card]:
        return self._cards.list_all()
