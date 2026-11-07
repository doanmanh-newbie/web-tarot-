from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.spreads.domain.spread import Spread, SpreadPosition
from app.modules.spreads.domain.spread_repository import SpreadRepository
from app.modules.spreads.infrastructure.models import SpreadModel


def _to_entity(m: SpreadModel) -> Spread:
    return Spread(
        id=m.id,
        slug=m.slug,
        name=m.name,
        description=m.description,
        positions=[SpreadPosition(p.position_index, p.label, p.description) for p in m.positions],
    )


class SqlAlchemySpreadRepository(SpreadRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Spread]:
        stmt = select(SpreadModel).options(selectinload(SpreadModel.positions)).order_by(SpreadModel.id)
        return [_to_entity(m) for m in self._session.scalars(stmt).all()]

    def get_by_id(self, spread_id: int) -> Spread | None:
        stmt = (
            select(SpreadModel)
            .where(SpreadModel.id == spread_id)
            .options(selectinload(SpreadModel.positions))
        )
        model = self._session.scalars(stmt).first()
        return _to_entity(model) if model else None
