"""Thống kê độ đúng người dùng tự chấm cho lời giải. Hàm thuần, không phụ thuộc framework, test được trực tiếp.

Chủ đề và đối tượng người hỏi không có cột riêng: frontend ghép vào đầu câu hỏi dạng
"Tôi là sinh viên. Chủ đề tình cảm: ...", nên tách lại bằng regex.
"""
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

_PREFIX = re.compile(r"^\s*(?:Tôi là (?P<persona>[^.]{1,60})\.\s*)?(?:Chủ đề (?P<topic>[^:]{1,30}):)?")
NO_PERSONA = "Không nói rõ"
NO_TOPIC = "Chung"
NO_VERSION = "v1 (trước khi lưu phiên bản)"
# (nhãn, điểm thấp nhất, điểm cao nhất) của từng nhóm điểm
BUCKETS = [("0–19%", 0, 19), ("20–39%", 20, 39), ("40–59%", 40, 59), ("60–79%", 60, 79), ("80–100%", 80, 100)]


@dataclass(frozen=True)
class RatingRow:
    """Một reading đã có lời giải (DONE), chưa xóa. accuracy None = người dùng chưa chấm."""

    spread_id: int
    question: str
    accuracy: int | None
    created_at: datetime
    prompt_version: str | None = None


@dataclass(frozen=True)
class GroupStat:
    name: str
    rated: int
    average: float | None  # None khi nhóm chưa có lượt chấm nào


@dataclass(frozen=True)
class DayStat:
    day: date
    rated: int
    average: float | None


@dataclass
class AccuracyStats:
    interpreted: int  # số lời giải đã có (có thể chấm)
    rated: int
    average: float | None
    buckets: list[GroupStat] = field(default_factory=list)  # average = None, chỉ dùng rated (số lượt)
    by_spread: list[GroupStat] = field(default_factory=list)
    by_topic: list[GroupStat] = field(default_factory=list)
    by_persona: list[GroupStat] = field(default_factory=list)
    by_version: list[GroupStat] = field(default_factory=list)  # so độ đúng trước/sau khi sửa prompt
    by_day: list[DayStat] = field(default_factory=list)

    @property
    def rating_rate(self) -> float:
        """Tỉ lệ lời giải được chấm, 0-100."""
        return round(self.rated * 100 / self.interpreted, 1) if self.interpreted else 0.0


def split_question(question: str) -> tuple[str, str]:
    """(đối tượng, chủ đề) tách từ phần đầu câu hỏi; không có thì trả nhãn mặc định."""
    m = _PREFIX.match(question)
    persona = (m.group("persona") or "").strip() if m else ""
    topic = (m.group("topic") or "").strip() if m else ""
    return (persona[:1].upper() + persona[1:]) if persona else NO_PERSONA, topic.capitalize() if topic else NO_TOPIC


def _avg(scores: list[int]) -> float | None:
    return round(sum(scores) / len(scores), 1) if scores else None


def _groups(pairs: list[tuple[str, int]]) -> list[GroupStat]:
    """Gom (nhóm, điểm) thành thống kê từng nhóm, nhiều lượt chấm nhất trước."""
    scores: dict[str, list[int]] = {}
    for name, score in pairs:
        scores.setdefault(name, []).append(score)
    stats = [GroupStat(name, len(v), _avg(v)) for name, v in scores.items()]
    return sorted(stats, key=lambda g: (-g.rated, g.name))


def summarize(
    rows: list[RatingRow], spread_names: dict[int, str], today: date, tz_name: str, days: int = 30
) -> AccuracyStats:
    rated = [r for r in rows if r.accuracy is not None]
    scores = [r.accuracy for r in rated]
    tz = ZoneInfo(tz_name)

    by_day: dict[date, list[int]] = {}
    for r in rated:
        by_day.setdefault(r.created_at.astimezone(tz).date(), []).append(r.accuracy)
    window = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]

    split = [(r, *split_question(r.question)) for r in rated]
    return AccuracyStats(
        interpreted=len(rows),
        rated=len(rated),
        average=_avg(scores),
        buckets=[GroupStat(label, sum(lo <= s <= hi for s in scores), None) for label, lo, hi in BUCKETS],
        by_spread=_groups([(spread_names.get(r.spread_id, f"Kiểu #{r.spread_id}"), r.accuracy) for r in rated]),
        by_topic=_groups([(topic, r.accuracy) for r, _, topic in split]),
        by_persona=_groups([(persona, r.accuracy) for r, persona, _ in split]),
        by_version=sorted(_groups([(r.prompt_version or NO_VERSION, r.accuracy) for r in rated]), key=lambda g: g.name),
        by_day=[DayStat(d, len(by_day.get(d, [])), _avg(by_day.get(d, []))) for d in window],
    )
