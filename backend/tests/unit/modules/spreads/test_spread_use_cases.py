import pytest

from app.modules.spreads.application.use_cases.get_spread import GetSpread
from app.modules.spreads.application.use_cases.list_spreads import ListSpreads
from app.modules.spreads.domain.exceptions import SpreadNotFound
from tests.unit.modules.spreads.fakes import FakeSpreadRepository, make_spread


def test_card_count_equals_number_of_positions():
    assert make_spread(labels=("Quá khứ", "Hiện tại", "Tương lai")).card_count == 3


def test_list_spreads():
    repo = FakeSpreadRepository([make_spread(2), make_spread(1)])
    assert [s.id for s in ListSpreads(repo).execute()] == [1, 2]


def test_get_spread():
    assert GetSpread(FakeSpreadRepository([make_spread(1)])).execute(1).slug == "spread-1"


def test_get_spread_not_found():
    with pytest.raises(SpreadNotFound):
        GetSpread(FakeSpreadRepository()).execute(5)
