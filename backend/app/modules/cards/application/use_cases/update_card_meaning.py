from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.domain.meaning_policy import clean_meaning


class UpdateCardMeaning:
    """Admin sửa ý nghĩa xuôi/ngược. Chỉ sửa nội dung, không đổi tên/loại/số của lá."""

    def __init__(self, cards: CardRepository) -> None:
        self._cards = cards

    def execute(self, card_id: int, upright_meaning: str, reversed_meaning: str) -> Card:
        upright = clean_meaning(upright_meaning, "Ý nghĩa xuôi")
        reversed_ = clean_meaning(reversed_meaning, "Ý nghĩa ngược")
        return self._cards.update_meaning(card_id, upright, reversed_)
