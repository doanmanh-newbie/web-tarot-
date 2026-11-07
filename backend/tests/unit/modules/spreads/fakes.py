from app.modules.spreads.domain.spread import Spread, SpreadPosition
from app.modules.spreads.domain.spread_repository import SpreadRepository


def make_spread(spread_id=1, labels=("A",)) -> Spread:
    return Spread(
        id=spread_id,
        slug=f"spread-{spread_id}",
        name=f"Spread {spread_id}",
        positions=[SpreadPosition(i, label) for i, label in enumerate(labels)],
    )


class FakeSpreadRepository(SpreadRepository):
    def __init__(self, spreads=None) -> None:
        self.spreads = {s.id: s for s in (spreads or [])}

    def list_all(self):
        return sorted(self.spreads.values(), key=lambda s: s.id)

    def get_by_id(self, spread_id):
        return self.spreads.get(spread_id)
