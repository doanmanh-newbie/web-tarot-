from datetime import datetime, timezone

from app.modules.quota.domain.quota_policy import build_status
from tests.unit.modules.readings.fakes import make_env

USER = 1


def test_fresh_user_has_full_quota():
    s = make_env(limit=3).quota.execute(USER)
    assert (s.limit, s.used, s.remaining, s.unlimited) == (3, 0, 3, False)


def test_quota_decreases_with_each_draw():
    env = make_env(limit=3)
    env.draw.execute(USER, 1, "q")
    s = env.quota.execute(USER)
    assert (s.used, s.remaining) == (1, 2)


def test_resets_at_is_next_midnight_vietnam_time():
    s = make_env().quota.execute(USER)  # 12:00 VN ngày 15/1
    assert s.resets_at.isoformat() == "2026-01-16T00:00:00+07:00"


def test_unlimited_user_has_no_limit_fields():
    env = make_env(limit=1)
    env.draw.execute(USER, 1, "q", unlimited=True)
    s = env.quota.execute(USER, unlimited=True)
    assert (s.limit, s.remaining, s.unlimited, s.used) == (None, None, True, 1)


def test_build_status_never_negative():
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert build_status(used=5, limit=3, window_end=end).remaining == 0
