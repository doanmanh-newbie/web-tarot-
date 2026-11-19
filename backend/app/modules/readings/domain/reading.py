from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AIStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


@dataclass
class DrawnCard:
    card_id: int
    position_index: int
    is_reversed: bool


@dataclass
class Reading:
    id: int | None
    user_id: int
    spread_id: int
    question: str
    drawn_cards: list[DrawnCard] = field(default_factory=list)
    ai_interpretation: str | None = None
    ai_status: AIStatus = AIStatus.PENDING
    created_at: datetime | None = None
    prompt_version: str | None = None  # phiên bản prompt sinh ra lời giải; None = trước khi có cột này
    accuracy: int | None = None  # người dùng tự chấm lời giải đúng bao nhiêu % (0-100); None = chưa chấm
