from app.modules.spreads.domain.exceptions import SpreadNotFound
from app.modules.spreads.domain.spread import Spread
from app.modules.spreads.domain.spread_repository import SpreadRepository


class GetSpread:
    def __init__(self, spreads: SpreadRepository) -> None:
        self._spreads = spreads

    def execute(self, spread_id: int) -> Spread:
        spread = self._spreads.get_by_id(spread_id)
        if spread is None:
            raise SpreadNotFound(str(spread_id))
        return spread
