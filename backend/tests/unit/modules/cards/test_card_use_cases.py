import pytest

from app.modules.cards.application.use_cases.get_card import GetCard
from app.modules.cards.application.use_cases.list_cards import ListCards
from app.modules.cards.application.use_cases.update_card_meaning import UpdateCardMeaning
from app.modules.cards.domain.exceptions import CardNotFound, InvalidCardMeaning
from app.modules.cards.domain.meaning_policy import MAX_LENGTH
from tests.unit.modules.cards.fakes import FakeCardRepository, make_card


@pytest.fixture
def repo():
    return FakeCardRepository([make_card(2), make_card(1)])


def test_list_cards_sorted_by_id(repo):
    assert [c.id for c in ListCards(repo).execute()] == [1, 2]


def test_get_card(repo):
    assert GetCard(repo).execute(1).slug == "card-1"


def test_get_card_not_found(repo):
    with pytest.raises(CardNotFound):
        GetCard(repo).execute(99)


def test_update_meaning_trims_and_saves(repo):
    card = UpdateCardMeaning(repo).execute(1, "  xuôi mới  ", " ngược mới ")
    assert card.upright_meaning == "xuôi mới"
    assert repo.get_by_id(1).reversed_meaning == "ngược mới"


def test_update_does_not_touch_other_fields(repo):
    before = repo.get_by_id(1)
    after = UpdateCardMeaning(repo).execute(1, "a", "b")
    assert (after.name, after.slug, after.arcana, after.number) == (
        before.name, before.slug, before.arcana, before.number,
    )


@pytest.mark.parametrize("upright,reversed_", [("", "ok"), ("ok", "   "), ("x" * (MAX_LENGTH + 1), "ok")])
def test_update_rejects_invalid_meaning(repo, upright, reversed_):
    with pytest.raises(InvalidCardMeaning):
        UpdateCardMeaning(repo).execute(1, upright, reversed_)
    assert repo.get_by_id(1).upright_meaning == "xuôi"  # không bị sửa dở


def test_update_unknown_card(repo):
    with pytest.raises(CardNotFound):
        UpdateCardMeaning(repo).execute(99, "a", "b")


def test_card_meaning_by_orientation():
    card = make_card(1)
    assert card.meaning(is_reversed=False) == "xuôi"
    assert card.meaning(is_reversed=True) == "ngược"
