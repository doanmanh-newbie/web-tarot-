from datetime import datetime, timezone

from app.modules.quota.domain.quota_policy import can_draw, day_bounds, remaining


def test_can_draw_under_limit():
    assert can_draw(used=2, limit=3)


def test_cannot_draw_at_limit():
    assert not can_draw(used=3, limit=3)


def test_remaining_never_negative():
    assert remaining(used=5, limit=3) == 0


def test_day_bounds_uses_vietnam_timezone():
    # 20:00 UTC ngày 1/1 = 03:00 ngày 2/1 giờ VN -> "hôm nay" phải bắt đầu từ 2/1
    now = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
    start, end = day_bounds(now, "Asia/Ho_Chi_Minh")
    assert start.day == 2 and start.hour == 0
    assert (end - start).days == 1
