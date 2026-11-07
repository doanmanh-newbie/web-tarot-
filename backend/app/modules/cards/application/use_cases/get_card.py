from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.domain.exceptions import CardNotFound


class GetCard:
    def __init__(self, cards: CardRepository) -> None:
        self._cards = cards

    def execute(self, card_id: int) -> Card:
        card = self._cards.get_by_id(card_id)
        if card is None:
            raise CardNotFound(str(card_id))
        return card
