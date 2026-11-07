import pytest

from app.modules.readings.domain.exceptions import ReadingNotFound
from app.modules.readings.domain.reading import AIStatus
from tests.unit.modules.readings.fakes import make_env

USER, OTHER = 1, 2


def failed_reading(env):
    env.ai.fail = True
    reading = env.draw.execute(USER, 1, "q").reading
    env.ai.fail = False
    return reading


def test_retry_succeeds_after_failure():
    env = make_env()
    r = failed_reading(env)
    assert env.interpret.execute(r.id, USER).reading.ai_status is AIStatus.DONE


def test_retry_that_fails_again_stays_failed_without_raising():
    env = make_env()
    r = failed_reading(env)
    env.ai.fail = True
    assert env.interpret.execute(r.id, USER).reading.ai_status is AIStatus.FAILED


def test_done_reading_is_not_sent_to_ai_again():
    env = make_env()
    r = env.draw.execute(USER, 1, "q").reading
    calls = len(env.ai.calls)
    again = env.interpret.execute(r.id, USER)
    assert len(env.ai.calls) == calls  # tiết kiệm quota Gemini
    assert again.reading.ai_interpretation == "Lời diễn giải thử nghiệm"


def test_blank_ai_answer_counts_as_failure():
    env = make_env()
    env.ai.text = "   "
    assert env.draw.execute(USER, 1, "q").reading.ai_status is AIStatus.FAILED


def test_cannot_interpret_someone_elses_reading():
    env = make_env()
    r = failed_reading(env)
    with pytest.raises(ReadingNotFound):
        env.interpret.execute(r.id, OTHER)


def test_unknown_reading():
    with pytest.raises(ReadingNotFound):
        make_env().interpret.execute(999, USER)


def test_ai_gets_spread_name_and_question():
    env = make_env()
    env.draw.execute(USER, 1, "Nên đổi việc không?")
    call = env.ai.calls[0]
    assert call.question == "Nên đổi việc không?" and call.spread_name == "Spread 1"
    assert call.cards[0].name == "Lá 1 (Card 1)"
