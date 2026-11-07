from app.modules.quota.application.ports.reading_counter import ReadingCounter
from app.modules.quota.domain.quota_policy import QuotaConfig, QuotaStatus, build_status, day_bounds
from app.shared.application.ports.clock import Clock


class GetQuota:
    """Số lượt đã dùng / còn lại hôm nay (hôm nay tính theo múi giờ cấu hình, mặc định UTC+7)."""

    def __init__(self, counter: ReadingCounter, clock: Clock, config: QuotaConfig) -> None:
        self._counter = counter
        self._clock = clock
        self._config = config

    def execute(self, user_id: int, unlimited: bool = False) -> QuotaStatus:
        start, end = day_bounds(self._clock.now(), self._config.tz_name)
        used = self._counter.count_by_user_between(user_id, start, end)
        return build_status(used, self._config.daily_limit, end, unlimited)
