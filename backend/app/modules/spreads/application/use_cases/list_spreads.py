from app.modules.spreads.domain.spread import Spread
from app.modules.spreads.domain.spread_repository import SpreadRepository


class ListSpreads:
    """Danh sách kiểu trải bài (kèm các vị trí)."""

    def __init__(self, spreads: SpreadRepository) -> None:
        self._spreads = spreads

    def execute(self) -> list[Spread]:
        return self._spreads.list_all()
