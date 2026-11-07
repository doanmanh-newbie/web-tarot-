from dataclasses import replace

from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.domain.exceptions import CardNotFound


def make_card(card_id=1, **overrides) -> Card:
    base = Card(
        id=card_id,
        slug=f"card-{card_id}",
        name=f"Card {card_id}",
        name_vi=f"Lá {card_id}",
        arcana="major",
        suit=None,
        number=card_id,
        upright_meaning="xuôi",
        reversed_meaning="ngược",
    )
    return replace(base, **overrides)


class FakeCardRepository(CardRepository):
    def __init__(self, cards=None) -> None:
        self.cards = {c.id: c for c in (cards or [])}

    def list_all(self):
        return sorted(self.cards.values(), key=lambda c: c.id)

    def list_ids(self):
        return sorted(self.cards)

    def get_by_id(self, card_id):
        return self.cards.get(card_id)

    def get_by_ids(self, card_ids):
        return [self.cards[i] for i in card_ids if i in self.cards]

    def update_meaning(self, card_id, upright, reversed_):
        if card_id not in self.cards:
            raise CardNotFound(str(card_id))
        self.cards[card_id] = replace(self.cards[card_id], upright_meaning=upright, reversed_meaning=reversed_)
        return self.cards[card_id]
