"""Lắp ráp module spreads: repository SQLAlchemy + use case."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.spreads.application.use_cases.get_spread import GetSpread
from app.modules.spreads.application.use_cases.list_spreads import ListSpreads
from app.modules.spreads.domain.spread_repository import SpreadRepository
from app.modules.spreads.infrastructure.sqlalchemy_spread_repository import SqlAlchemySpreadRepository
from app.shared.presentation.dependencies import get_db_session


def get_spread_repository(session: Session = Depends(get_db_session)) -> SpreadRepository:
    return SqlAlchemySpreadRepository(session)


def get_list_spreads(spreads: SpreadRepository = Depends(get_spread_repository)) -> ListSpreads:
    return ListSpreads(spreads)


def get_get_spread(spreads: SpreadRepository = Depends(get_spread_repository)) -> GetSpread:
    return GetSpread(spreads)
