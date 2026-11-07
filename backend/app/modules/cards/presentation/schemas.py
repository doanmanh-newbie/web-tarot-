from pydantic import BaseModel, ConfigDict, Field

from app.modules.cards.domain.card import Card
from app.modules.cards.domain.meaning_policy import MAX_LENGTH


class CardResponse(BaseModel):
    id: int
    slug: str
    name: str
    name_vi: str
    arcana: str
    suit: str | None
    number: int
    upright_meaning: str
    reversed_meaning: str
    image_url: str | None

    @classmethod
    def from_entity(cls, card: Card) -> "CardResponse":
        return cls(**card.__dict__)


class UpdateCardMeaningRequest(BaseModel):
    # forbid: chỉ cho sửa ý nghĩa, gửi thêm field khác (name, arcana...) sẽ bị 422
    model_config = ConfigDict(extra="forbid")

    upright_meaning: str = Field(min_length=1, max_length=MAX_LENGTH + 200)
    reversed_meaning: str = Field(min_length=1, max_length=MAX_LENGTH + 200)
