from abc import ABC, abstractmethod

from app.modules.spreads.domain.spread import Spread


class SpreadRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Spread]: ...

    @abstractmethod
    def get_by_id(self, spread_id: int) -> Spread | None: ...
