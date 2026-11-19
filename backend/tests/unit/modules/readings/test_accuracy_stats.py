from datetime import date, datetime, timezone

from app.modules.readings.domain.accuracy_stats import NO_PERSONA, NO_TOPIC, RatingRow, split_question, summarize
from tests.unit.modules.readings.fakes import make_env

TZ = "Asia/Ho_Chi_Minh"
TODAY = date(2026, 1, 15)
NAMES = {1: "Ba lá", 2: "Ba lá tự do"}


def row(spread, question, accuracy, day=15, hour=5):
    return RatingRow(spread, question, accuracy, datetime(2026, 1, day, hour, tzinfo=timezone.utc))


def test_split_question_reads_persona_and_topic_prefixes():
    assert split_question("Tôi là sinh viên. Chủ đề tình cảm: có người yêu không") == ("Sinh viên", "Tình cảm")
    assert split_question("Chủ đề tài chính: tháng này thế nào") == (NO_PERSONA, "Tài chính")
    assert split_question("Tôi là chủ quán, người kinh doanh nhỏ. Doanh thu?") == (
        "Chủ quán, người kinh doanh nhỏ",
        NO_TOPIC,
    )
    assert split_question("Tuần này tôi nên làm gì?") == (NO_PERSONA, NO_TOPIC)


def test_summary_counts_averages_and_groups():
    rows = [
        row(1, "Tôi là sinh viên. Chủ đề tình cảm: a", 80),
        row(1, "Tôi là sinh viên. b", 60),
        row(2, "Chủ đề tình cảm: c", 100),
        row(2, "d", None),  # có lời giải nhưng chưa chấm
    ]
    s = summarize(rows, NAMES, TODAY, TZ, days=7)
    assert (s.interpreted, s.rated, s.average, s.rating_rate) == (4, 3, 80.0, 75.0)
    assert [(b.name, b.rated) for b in s.buckets][-2:] == [("60–79%", 1), ("80–100%", 2)]
    assert {g.name: (g.rated, g.average) for g in s.by_spread} == {"Ba lá": (2, 70.0), "Ba lá tự do": (1, 100.0)}
    assert {g.name: g.average for g in s.by_topic} == {"Tình cảm": 90.0, NO_TOPIC: 60.0}
    assert s.by_persona[0].name == "Sinh viên" and s.by_persona[0].rated == 2


def test_by_day_covers_the_window_in_local_time_and_fills_empty_days():
    # 18:00 UTC ngày 14 = 01:00 ngày 15 giờ Việt Nam
    rows = [row(1, "a", 50, day=14, hour=18), row(1, "b", 90, day=13, hour=3)]
    s = summarize(rows, NAMES, TODAY, TZ, days=3)
    assert [(d.day.day, d.rated, d.average) for d in s.by_day] == [(13, 1, 90.0), (14, 0, None), (15, 1, 50.0)]


def test_empty_data_has_no_average():
    s = summarize([], NAMES, TODAY, TZ)
    assert (s.interpreted, s.rated, s.average, s.rating_rate) == (0, 0, None, 0.0)
    assert len(s.by_day) == 30


def test_repository_only_feeds_interpreted_and_not_deleted_readings():
    env = make_env(limit=10)
    keep = env.draw.execute(1, 1, "Công việc?").reading.id
    env.rate.execute(keep, 1, 40)
    env.draw.execute(1, 1, "Chưa giải?", interpret=False)
    gone = env.draw.execute(1, 1, "Sẽ xóa").reading.id
    env.delete.execute(gone, 1)
    assert [(r.question, r.accuracy) for r in env.readings.list_interpreted()] == [("Công việc?", 40)]


def test_stats_compare_prompt_versions():
    rows = [
        RatingRow(1, "a", 40, datetime(2026, 1, 15, tzinfo=timezone.utc)),
        RatingRow(1, "b", 80, datetime(2026, 1, 15, tzinfo=timezone.utc), "v2"),
        RatingRow(1, "c", 60, datetime(2026, 1, 15, tzinfo=timezone.utc), "v2"),
    ]
    s = summarize(rows, NAMES, TODAY, TZ)
    expected = [("v1 (trước khi lưu phiên bản)", 1, 40.0), ("v2", 2, 70.0)]
    assert [(g.name, g.rated, g.average) for g in s.by_version] == expected
