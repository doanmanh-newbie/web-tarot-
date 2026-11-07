"""Bản giả để test use case của readings/quota không cần DB, mạng hay Gemini thật."""
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

from app.modules.cards.domain.card import Card
from app.modules.quota.application.ports.reading_counter import ReadingCounter
from app.modules.quota.application.use_cases.get_quota import GetQuota
from app.modules.quota.domain.quota_policy import QuotaConfig
from app.modules.readings.application.ports.ai_interpreter import AIInterpreter
from app.modules.readings.application.ports.random_source import RandomSource
from app.modules.readings.application.reading_details import ReadingDetailsBuilder
from app.modules.readings.application.use_cases.delete_reading import DeleteReading
from app.modules.readings.application.use_cases.draw_reading import DrawReading
from app.modules.readings.application.use_cases.get_reading import GetReading
from app.modules.readings.application.use_cases.interpret_reading import InterpretReading
from app.modules.readings.application.use_cases.list_readings import ListReadings
from app.modules.readings.domain.exceptions import InterpretationFailed
from app.modules.readings.domain.reading import AIStatus, Reading
from app.modules.readings.domain.reading_repository import ReadingRepository
from app.shared.application.ports.clock import Clock
from tests.unit.modules.cards.fakes import FakeCardRepository, make_card
from tests.unit.modules.spreads.fakes import FakeSpreadRepository, make_spread

TZ = "Asia/Ho_Chi_Minh"


class FakeClock(Clock):
    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at


class FakeRandomSource(RandomSource):
    """Bốc các lá đầu danh sách, chiều bài xen kẽ: xuôi, ngược, xuôi, ..."""

    def draw_cards(self, deck_ids, count):
        return [(deck_ids[i], i % 2 == 1) for i in range(count)]


class FakeAI(AIInterpreter):
    def __init__(self, fail: bool = False, text: str = "Lời diễn giải thử nghiệm") -> None:
        self.fail = fail
        self.text = text
        self.calls = []

    def interpret(self, question, spread_name, cards):
        self.calls.append(SimpleNamespace(question=question, spread_name=spread_name, cards=cards))
        if self.fail:
            raise InterpretationFailed("fake lỗi")
        return self.text


class FakeReadingRepository(ReadingRepository, ReadingCounter):
    def __init__(self) -> None:
        self.rows: dict[int, Reading] = {}
        self.deleted: set[int] = set()
        self._next_id = 1

    def count_by_user_between(self, user_id, start, end):
        # giống bản thật: reading đã xóa vẫn được đếm
        return sum(1 for r in self.rows.values() if r.user_id == user_id and start <= r.created_at < end)

    def add_if_under_limit(self, reading, limit, window_start, window_end):
        if limit is not None and self.count_by_user_between(reading.user_id, window_start, window_end) >= limit:
            return None
        saved = replace(reading, id=self._next_id, ai_status=AIStatus.PENDING)
        self.rows[saved.id] = saved
        self._next_id += 1
        return saved

    def get_by_id(self, reading_id):
        return None if reading_id in self.deleted else self.rows.get(reading_id)

    def list_by_user(self, user_id, limit=20, offset=0):
        mine = [r for r in self.rows.values() if r.user_id == user_id and r.id not in self.deleted]
        mine.sort(key=lambda r: (r.created_at, r.id), reverse=True)
        return mine[offset : offset + limit]

    def update_interpretation(self, reading_id, text, status):
        self.rows[reading_id] = replace(self.rows[reading_id], ai_interpretation=text, ai_status=status)
        return self.rows[reading_id]

    def delete(self, reading_id):
        self.deleted.add(reading_id)


def make_env(limit=3, ai_fails=False, now=None, deck_size=78, labels=("Quá khứ", "Hiện tại", "Tương lai")):
    clock = FakeClock(now or datetime(2026, 1, 15, 5, 0, tzinfo=timezone.utc))  # 12:00 giờ VN
    cards: list[Card] = [make_card(i) for i in range(1, deck_size + 1)]
    cards_repo = FakeCardRepository(cards)
    spreads_repo = FakeSpreadRepository([make_spread(1, labels)])
    readings = FakeReadingRepository()
    ai = FakeAI(fail=ai_fails)
    builder = ReadingDetailsBuilder(spreads_repo, cards_repo)
    interpret = InterpretReading(readings, builder, ai)
    config = QuotaConfig(daily_limit=limit, tz_name=TZ)
    return SimpleNamespace(
        clock=clock,
        ai=ai,
        readings=readings,
        cards=cards_repo,
        spreads=spreads_repo,
        interpret=interpret,
        draw=DrawReading(spreads_repo, cards_repo, readings, FakeRandomSource(), interpret, clock, config, 300),
        quota=GetQuota(readings, clock, config),
        list=ListReadings(readings, builder),
        get=GetReading(readings, builder),
        delete=DeleteReading(readings),
    )
