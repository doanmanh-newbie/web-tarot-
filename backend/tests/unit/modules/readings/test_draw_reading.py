from datetime import datetime, timedelta, timezone

import pytest

from app.modules.quota.domain.exceptions import DailyQuotaExceeded
from app.modules.readings.domain.exceptions import DeckNotReady, InvalidQuestion
from app.modules.readings.domain.reading import AIStatus
from app.modules.spreads.domain.exceptions import SpreadNotFound
from tests.unit.modules.readings.fakes import make_env

USER, OTHER = 1, 2


def test_draw_gives_one_card_per_position_and_interprets():
    env = make_env()
    d = env.draw.execute(USER, 1, "Công việc sắp tới thế nào?")
    assert [c.position_label for c in d.cards] == ["Quá khứ", "Hiện tại", "Tương lai"]
    assert [c.position_index for c in d.cards] == [0, 1, 2]
    assert d.reading.ai_status is AIStatus.DONE
    assert d.reading.ai_interpretation == "Lời diễn giải thử nghiệm"
    assert d.reading.id is not None and d.reading.user_id == USER


def test_question_is_cleaned_before_saving():
    env = make_env()
    assert env.draw.execute(USER, 1, "  hỏi   gì đó  ").reading.question == "hỏi gì đó"


def test_created_at_comes_from_the_clock():
    env = make_env()
    assert env.draw.execute(USER, 1, "q").reading.created_at == env.clock.at


def test_ai_receives_meaning_matching_orientation_and_position():
    env = make_env()
    env.draw.execute(USER, 1, "q")
    cards = env.ai.calls[0].cards
    assert [c.is_reversed for c in cards] == [False, True, False]
    assert [c.base_meaning for c in cards] == ["xuôi", "ngược", "xuôi"]  # ý nghĩa lấy từ DB, đúng chiều bài
    assert [c.position_label for c in cards] == ["Quá khứ", "Hiện tại", "Tương lai"]


# ---------------------------------------------------------------- quota
def test_fourth_draw_in_a_day_is_blocked():
    env = make_env(limit=3)
    for _ in range(3):
        env.draw.execute(USER, 1, "q")
    with pytest.raises(DailyQuotaExceeded):
        env.draw.execute(USER, 1, "q")
    assert env.quota.execute(USER).remaining == 0


def test_blocked_draw_does_not_call_ai_or_save():
    env = make_env(limit=1)
    env.draw.execute(USER, 1, "q")
    calls_before = len(env.ai.calls)
    with pytest.raises(DailyQuotaExceeded):
        env.draw.execute(USER, 1, "q")
    assert len(env.ai.calls) == calls_before and len(env.readings.rows) == 1


def test_quota_is_per_user():
    env = make_env(limit=1)
    env.draw.execute(USER, 1, "q")
    assert env.draw.execute(OTHER, 1, "q").reading.user_id == OTHER


def test_admin_is_unlimited():
    env = make_env(limit=1)
    for _ in range(5):
        env.draw.execute(USER, 1, "q", unlimited=True)
    assert len(env.readings.rows) == 5


def test_quota_resets_at_midnight_vietnam_time():
    # 16:59 UTC = 23:59 giờ VN (vẫn là ngày cũ); 17:00 UTC = 00:00 giờ VN (ngày mới)
    env = make_env(limit=1, now=datetime(2026, 1, 15, 16, 59, tzinfo=timezone.utc))
    env.draw.execute(USER, 1, "q")
    with pytest.raises(DailyQuotaExceeded):
        env.draw.execute(USER, 1, "q")
    env.clock.at = datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)
    assert env.draw.execute(USER, 1, "q").reading.id is not None


def test_one_minute_before_midnight_still_old_day():
    env = make_env(limit=1, now=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc))  # 07:00 VN
    env.draw.execute(USER, 1, "q")
    env.clock.at += timedelta(hours=16, minutes=58)  # 23:58 VN
    with pytest.raises(DailyQuotaExceeded):
        env.draw.execute(USER, 1, "q")


# ---------------------------------------------------------------- lỗi đầu vào không mất lượt
@pytest.mark.parametrize("question", ["", "   ", "x" * 301])
def test_invalid_question_does_not_consume_quota(question):
    env = make_env(limit=3)
    with pytest.raises(InvalidQuestion):
        env.draw.execute(USER, 1, question)
    assert env.quota.execute(USER).used == 0 and not env.readings.rows


def test_unknown_spread_does_not_consume_quota():
    env = make_env()
    with pytest.raises(SpreadNotFound):
        env.draw.execute(USER, 99, "q")
    assert env.quota.execute(USER).used == 0


def test_unseeded_deck_is_reported_not_crashed():
    env = make_env(deck_size=2)  # kiểu 3 lá nhưng chỉ có 2 lá trong DB
    with pytest.raises(DeckNotReady):
        env.draw.execute(USER, 1, "q")
    assert env.quota.execute(USER).used == 0


# ---------------------------------------------------------------- AI lỗi
def test_ai_failure_keeps_the_reading_and_counts_the_draw():
    env = make_env(ai_fails=True)
    d = env.draw.execute(USER, 1, "q")
    assert d.reading.ai_status is AIStatus.FAILED and d.reading.ai_interpretation is None
    assert len(d.cards) == 3  # bài vẫn còn, không mất
    assert env.quota.execute(USER).used == 1  # người dùng đã rút bài nên lượt được tính


def test_retry_after_ai_failure_costs_no_extra_quota_and_keeps_same_cards():
    env = make_env(ai_fails=True, limit=3)
    failed = env.draw.execute(USER, 1, "q")
    env.ai.fail = False
    retried = env.interpret.execute(failed.reading.id, USER)
    assert retried.reading.ai_status is AIStatus.DONE
    assert [(c.card.id, c.is_reversed) for c in retried.cards] == [(c.card.id, c.is_reversed) for c in failed.cards]
    assert env.quota.execute(USER).used == 1
