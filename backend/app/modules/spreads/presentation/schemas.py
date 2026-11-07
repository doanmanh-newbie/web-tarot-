from pydantic import BaseModel

from app.modules.spreads.domain.spread import Spread


class SpreadPositionResponse(BaseModel):
    index: int
    label: str
    description: str


class SpreadResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    card_count: int
    positions: list[SpreadPositionResponse]

    @classmethod
    def from_entity(cls, spread: Spread) -> "SpreadResponse":
        return cls(
            id=spread.id,
            slug=spread.slug,
            name=spread.name,
            description=spread.description,
            card_count=spread.card_count,
            positions=[
                SpreadPositionResponse(index=p.index, label=p.label, description=p.description)
                for p in spread.positions
            ],
        )
