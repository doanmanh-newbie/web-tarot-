import pytest

from app.modules.readings.infrastructure.secure_random_source import SecureRandomSource

DECK = list(range(1, 79))


def test_draws_requested_number_without_duplicates():
    src = SecureRandomSource()
    for _ in range(200):
        picked = src.draw_cards(DECK, 5)
        ids = [card_id for card_id, _ in picked]
        assert len(ids) == 5 and len(set(ids)) == 5 and set(ids) <= set(DECK)


def test_can_draw_whole_deck():
    assert sorted(i for i, _ in SecureRandomSource().draw_cards(DECK, 78)) == DECK


def test_both_orientations_occur_roughly_evenly():
    src = SecureRandomSource()
    flags = [rev for _ in range(500) for _, rev in src.draw_cards(DECK, 3)]
    reversed_share = sum(flags) / len(flags)
    assert 0.4 < reversed_share < 0.6  # 1500 lần tung, lệch xa 50% gần như không thể xảy ra


def test_every_card_can_be_drawn():
    src = SecureRandomSource()
    seen = {i for _ in range(600) for i, _ in src.draw_cards(DECK, 3)}
    assert len(seen) > 70  # 1800 lần bốc, hầu hết các lá phải xuất hiện


def test_too_many_cards_requested():
    with pytest.raises(ValueError):
        SecureRandomSource().draw_cards([1, 2], 3)
