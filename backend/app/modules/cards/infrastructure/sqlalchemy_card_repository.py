from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.domain.exceptions import CardNotFound
from app.modules.cards.infrastructure.models import CardModel


def _to_entity(m: CardModel) -> Card:
    return Card(
        id=m.id,
        slug=m.slug,
        name=m.name,
        name_vi=m.name_vi,
        arcana=m.arcana,
        suit=m.suit,
        number=m.number,
        upright_meaning=m.upright_meaning,
        reversed_meaning=m.reversed_meaning,
        image_url=m.image_url,
    )


class SqlAlchemyCardRepository(CardRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Card]:
        rows = self._session.scalars(select(CardModel).order_by(CardModel.id)).all()
        return [_to_entity(r) for r in rows]

    def list_ids(self) -> list[int]:
        return list(self._session.scalars(select(CardModel.id).order_by(CardModel.id)).all())

    def get_by_id(self, card_id: int) -> Card | None:
        model = self._session.get(CardModel, card_id)
        return _to_entity(model) if model else None

    def get_by_ids(self, card_ids: list[int]) -> list[Card]:
        if not card_ids:
            return []
        rows = self._session.scalars(select(CardModel).where(CardModel.id.in_(card_ids))).all()
        by_id = {r.id: _to_entity(r) for r in rows}
        return [by_id[i] for i in card_ids if i in by_id]

    def update_meaning(self, card_id: int, upright: str, reversed_: str) -> Card:
        model = self._session.get(CardModel, card_id)
        if model is None:
            raise CardNotFound(str(card_id))
        model.upright_meaning = upright
        model.reversed_meaning = reversed_
        self._session.commit()
        return _to_entity(model)
