"""Luật quota thuần (không phụ thuộc DB/HTTP) - dễ unit test."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class QuotaConfig:
    daily_limit: int
    tz_name: str


@dataclass(frozen=True)
class QuotaStatus:
    limit: int | None        # None = không giới hạn
    used: int
    remaining: int | None    # None = không giới hạn
    resets_at: datetime      # 00:00 ngày mai theo múi giờ cấu hình
    unlimited: bool


def day_bounds(now: datetime, tz_name: str) -> tuple[datetime, datetime]:
    """Trả về [00:00 hôm nay, 00:00 ngày mai) theo múi giờ cấu hình."""
    tz = ZoneInfo(tz_name)
    local_now = now.astimezone(tz)
    start = datetime.combine(local_now.date(), time.min, tzinfo=tz)
    return start, start + timedelta(days=1)


def remaining(used: int, limit: int) -> int:
    return max(limit - used, 0)


def can_draw(used: int, limit: int) -> bool:
    return used < limit


def build_status(used: int, limit: int, window_end: datetime, unlimited: bool = False) -> QuotaStatus:
    if unlimited:
        return QuotaStatus(limit=None, used=used, remaining=None, resets_at=window_end, unlimited=True)
    return QuotaStatus(
        limit=limit, used=used, remaining=remaining(used, limit), resets_at=window_end, unlimited=False
    )
