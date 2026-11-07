from fastapi import APIRouter, Depends

from app.modules.auth.presentation.dependencies import require_admin
from app.modules.cards.application.use_cases.get_card import GetCard
from app.modules.cards.application.use_cases.list_cards import ListCards
from app.modules.cards.application.use_cases.update_card_meaning import UpdateCardMeaning
from app.modules.cards.presentation.dependencies import (
    get_get_card,
    get_list_cards,
    get_update_card_meaning,
)
from app.modules.cards.presentation.schemas import CardResponse, UpdateCardMeaningRequest

# Toàn bộ router chỉ dành cho admin
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[CardResponse])
def list_cards(use_case: ListCards = Depends(get_list_cards)) -> list[CardResponse]:
    return [CardResponse.from_entity(c) for c in use_case.execute()]


@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int, use_case: GetCard = Depends(get_get_card)) -> CardResponse:
    return CardResponse.from_entity(use_case.execute(card_id))


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    body: UpdateCardMeaningRequest,
    use_case: UpdateCardMeaning = Depends(get_update_card_meaning),
) -> CardResponse:
    card = use_case.execute(card_id, body.upright_meaning, body.reversed_meaning)
    return CardResponse.from_entity(card)
