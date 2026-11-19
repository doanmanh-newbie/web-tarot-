from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.quota.domain.quota_policy import QuotaStatus
from app.modules.readings.application.reading_details import ReadingDetails
from app.modules.readings.domain.accuracy_stats import AccuracyStats, GroupStat

DISCLAIMER = "Nội dung chỉ mang tính giải trí và tham khảo, không thay thế lời khuyên của chuyên gia."


class DrawReadingRequest(BaseModel):
    # forbid: không nhận field lạ. max_length chỉ chặn body quá lớn; giới hạn thật (300) nằm ở domain.
    model_config = ConfigDict(extra="forbid")

    spread_id: int
    question: str = Field(min_length=1, max_length=2000)


class RateReadingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accuracy: int = Field(ge=0, le=100)  # lời giải đúng bao nhiêu % theo cảm nhận của người dùng


class CardSummary(BaseModel):
    id: int
    slug: str
    name: str
    name_vi: str
    image_url: str | None


class DrawnCardResponse(BaseModel):
    position_index: int
    position_label: str
    is_reversed: bool
    meaning: str  # ý nghĩa gốc đúng chiều xuôi/ngược
    card: CardSummary


class SpreadSummary(BaseModel):
    id: int
    name: str


class ReadingResponse(BaseModel):
    id: int
    spread: SpreadSummary
    question: str
    created_at: datetime
    ai_status: str                      # "done" | "failed" | "pending"
    ai_interpretation: str | None       # null khi chưa có: hiện nút "Giải lại"
    cards: list[DrawnCardResponse]
    accuracy: int | None = None         # % người dùng tự chấm; null = chưa chấm
    disclaimer: str = DISCLAIMER

    @classmethod
    def from_details(cls, d: ReadingDetails) -> "ReadingResponse":
        r = d.reading
        return cls(
            id=r.id,
            spread=SpreadSummary(id=d.spread.id, name=d.spread.name),
            question=r.question,
            created_at=r.created_at,
            ai_status=r.ai_status.value,
            ai_interpretation=r.ai_interpretation,
            accuracy=r.accuracy,
            cards=[
                DrawnCardResponse(
                    position_index=c.position_index,
                    position_label=c.position_label,
                    is_reversed=c.is_reversed,
                    meaning=c.meaning,
                    card=CardSummary(
                        id=c.card.id,
                        slug=c.card.slug,
                        name=c.card.name,
                        name_vi=c.card.name_vi,
                        image_url=c.card.image_url,
                    ),
                )
                for c in d.cards
            ],
        )


class QuotaResponse(BaseModel):
    limit: int | None        # null = không giới hạn (admin)
    used: int
    remaining: int | None
    resets_at: datetime
    unlimited: bool

    @classmethod
    def from_status(cls, s: QuotaStatus) -> "QuotaResponse":
        return cls(limit=s.limit, used=s.used, remaining=s.remaining, resets_at=s.resets_at, unlimited=s.unlimited)


class GroupStatResponse(BaseModel):
    name: str
    rated: int
    average: float | None

    @classmethod
    def many(cls, items: list[GroupStat]) -> list["GroupStatResponse"]:
        return [cls(name=g.name, rated=g.rated, average=g.average) for g in items]


class DayStatResponse(BaseModel):
    day: date
    rated: int
    average: float | None


class AccuracyStatsResponse(BaseModel):
    interpreted: int          # số lời giải đã có (có thể chấm)
    rated: int                # số lời giải đã được người dùng chấm
    rating_rate: float        # % lời giải được chấm
    average: float | None     # độ đúng trung bình (%)
    buckets: list[GroupStatResponse]
    by_spread: list[GroupStatResponse]
    by_topic: list[GroupStatResponse]
    by_persona: list[GroupStatResponse]
    by_version: list[GroupStatResponse]  # độ đúng theo phiên bản prompt
    by_day: list[DayStatResponse]

    @classmethod
    def from_stats(cls, s: AccuracyStats) -> "AccuracyStatsResponse":
        return cls(
            interpreted=s.interpreted,
            rated=s.rated,
            rating_rate=s.rating_rate,
            average=s.average,
            buckets=GroupStatResponse.many(s.buckets),
            by_spread=GroupStatResponse.many(s.by_spread),
            by_topic=GroupStatResponse.many(s.by_topic),
            by_persona=GroupStatResponse.many(s.by_persona),
            by_version=GroupStatResponse.many(s.by_version),
            by_day=[DayStatResponse(day=d.day, rated=d.rated, average=d.average) for d in s.by_day],
        )
