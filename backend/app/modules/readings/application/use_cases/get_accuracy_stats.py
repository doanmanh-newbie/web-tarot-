from zoneinfo import ZoneInfo

from app.modules.readings.domain.accuracy_stats import AccuracyStats, summarize
from app.modules.readings.domain.reading_repository import ReadingRepository
from app.modules.spreads.domain.spread_repository import SpreadRepository
from app.shared.application.ports.clock import Clock


class GetAccuracyStats:
    """Thống kê độ đúng người dùng tự chấm, cho trang thống kê của admin (toàn bộ người dùng)."""

    def __init__(self, readings: ReadingRepository, spreads: SpreadRepository, clock: Clock, tz_name: str) -> None:
        self._readings = readings
        self._spreads = spreads
        self._clock = clock
        self._tz_name = tz_name

    def execute(self, days: int = 30) -> AccuracyStats:
        today = self._clock.now().astimezone(ZoneInfo(self._tz_name)).date()
        names = {s.id: s.name for s in self._spreads.list_all()}
        return summarize(self._readings.list_interpreted(), names, today, self._tz_name, days)
