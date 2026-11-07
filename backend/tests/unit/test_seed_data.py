"""Kiểm tra file dữ liệu seed: gõ sai/thiếu/trùng thì test đỏ ngay, khỏi phát hiện lúc demo."""
import copy

from scripts.seed_cards import load_data, validate_cards, validate_spreads


def test_cards_json_is_valid():
    cards, _ = load_data()
    assert validate_cards(cards) == []


def test_spreads_json_is_valid():
    _, spreads = load_data()
    assert validate_spreads(spreads) == []


def test_deck_composition():
    cards, _ = load_data()
    assert len(cards) == 78
    assert sum(c["arcana"] == "major" for c in cards) == 22
    for suit in ("wands", "cups", "swords", "pentacles"):
        assert sum(c["suit"] == suit for c in cards) == 14


def test_every_card_has_both_meanings_and_image_path():
    cards, _ = load_data()
    for c in cards:
        assert len(c["upright_meaning"]) >= 20 and len(c["reversed_meaning"]) >= 20, c["slug"]
        assert c["image_url"] == f"/cards/{c['slug']}.jpg"


def test_upright_and_reversed_differ():
    cards, _ = load_data()
    assert all(c["upright_meaning"] != c["reversed_meaning"] for c in cards)


def test_validator_catches_missing_card():
    cards, _ = load_data()
    assert validate_cards(cards[:-1])


def test_validator_catches_duplicate_slug():
    cards, _ = load_data()
    broken = copy.deepcopy(cards)
    broken[1]["slug"] = broken[0]["slug"]
    assert any("Trùng slug" in e for e in validate_cards(broken))


def test_validator_catches_empty_meaning():
    cards, _ = load_data()
    broken = copy.deepcopy(cards)
    broken[5]["reversed_meaning"] = " "
    assert validate_cards(broken)


def test_validator_catches_bad_suit():
    cards, _ = load_data()
    broken = copy.deepcopy(cards)
    broken[30]["suit"] = "coins"
    assert validate_cards(broken)
