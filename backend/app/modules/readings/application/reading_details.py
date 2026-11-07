"""Reading kèm thông tin lá bài và kiểu trải bài, sẵn để hiển thị.

Entity `Reading` chỉ giữ id; muốn hiện tên lá, ảnh, nhãn vị trí thì cần ghép thêm. `ReadingDetailsBuilder`
làm việc đó và lấy dữ liệu theo lô (không truy vấn từng reading một).
"""
from dataclasses import dataclass

from app.modules.cards.domain.card import Card
from app.modules.cards.domain.card_repository import CardRepository
from app.modules.cards.domain.exceptions import CardNotFound
from app.modules.readings.domain.reading import Reading
from app.modules.spreads.domain.exceptions import SpreadNotFound
from app.modules.spreads.domain.spread import Spread
from app.modules.spreads.domain.spread_repository import SpreadRepository


@dataclass
class DrawnCardDetails:
    position_index: int
    position_label: str
    position_description: str
    is_reversed: bool
    card: Card

    @property
    def meaning(self) -> str:
        return self.card.meaning(self.is_reversed)


@dataclass
class ReadingDetails:
    reading: Reading
    spread: Spread
    cards: list[DrawnCardDetails]


class ReadingDetailsBuilder:
    def __init__(self, spreads: SpreadRepository, cards: CardRepository) -> None:
        self._spreads = spreads
        self._cards = cards

    def build(self, reading: Reading) -> ReadingDetails:
        return self.build_many([reading])[0]

    def build_many(self, readings: list[Reading]) -> list[ReadingDetails]:
        if not readings:
            return []
        spreads_by_id = {s.id: s for s in self._spreads.list_all()}
        card_ids = sorted({d.card_id for r in readings for d in r.drawn_cards})
        cards_by_id = {c.id: c for c in self._cards.get_by_ids(card_ids)}
        return [self._assemble(r, spreads_by_id, cards_by_id) for r in readings]

    @staticmethod
    def _assemble(reading: Reading, spreads_by_id: dict, cards_by_id: dict) -> ReadingDetails:
        spread = spreads_by_id.get(reading.spread_id)
        if spread is None:
            raise SpreadNotFound(str(reading.spread_id))
        positions = {p.index: p for p in spread.positions}
        details = []
        for drawn in sorted(reading.drawn_cards, key=lambda d: d.position_index):
            card = cards_by_id.get(drawn.card_id)
            if card is None:
                raise CardNotFound(str(drawn.card_id))
            position = positions.get(drawn.position_index)
            details.append(
                DrawnCardDetails(
                    position_index=drawn.position_index,
                    position_label=position.label if position else f"Vị trí {drawn.position_index + 1}",
                    position_description=position.description if position else "",
                    is_reversed=drawn.is_reversed,
                    card=card,
                )
            )
        return ReadingDetails(reading=reading, spread=spread, cards=details)
