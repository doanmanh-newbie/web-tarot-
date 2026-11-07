"""Lắp ráp module cards: repository SQLAlchemy + use case."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.cards.application.use_cases.get_card import GetCard
from app.modules.cards.application.use_cases.list_cards import ListCards
from app.modules.cards.application.use_cases.update_card_meaning import UpdateCardMeaning
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.infrastructure.sqlalchemy_card_repository import SqlAlchemyCardRepository
from app.shared.presentation.dependencies import get_db_session


def get_card_repository(session: Session = Depends(get_db_session)) -> CardRepository:
    return SqlAlchemyCardRepository(session)


def get_list_cards(cards: CardRepository = Depends(get_card_repository)) -> ListCards:
    return ListCards(cards)


def get_get_card(cards: CardRepository = Depends(get_card_repository)) -> GetCard:
    return GetCard(cards)


def get_update_card_meaning(cards: CardRepository = Depends(get_card_repository)) -> UpdateCardMeaning:
    return UpdateCardMeaning(cards)
