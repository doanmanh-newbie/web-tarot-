import pytest

from app.modules.readings.domain.exceptions import InvalidAccuracy, ReadingNotFound
from tests.unit.modules.readings.fakes import make_env

USER, OTHER = 1, 2


def drawn(env, **kw):
    return env.draw.execute(USER, 1, "Công việc sắp tới thế nào?", **kw).reading.id


def test_owner_rates_and_can_change_the_score():
    env = make_env()
    rid = drawn(env)
    assert env.rate.execute(rid, USER, 70).reading.accuracy == 70
    assert env.rate.execute(rid, USER, 100).reading.accuracy == 100
    assert env.get.execute(rid, USER).reading.accuracy == 100


def test_new_reading_is_unrated():
    env = make_env()
    assert env.get.execute(drawn(env), USER).reading.accuracy is None


@pytest.mark.parametrize("score", [-1, 101])
def test_score_outside_0_to_100_is_rejected(score):
    env = make_env()
    with pytest.raises(InvalidAccuracy):
        env.rate.execute(drawn(env), USER, score)


def test_cannot_rate_someone_elses_reading():
    env = make_env()
    with pytest.raises(ReadingNotFound):
        env.rate.execute(drawn(env), OTHER, 50)


def test_cannot_rate_before_there_is_an_interpretation():
    env = make_env()
    with pytest.raises(InvalidAccuracy):
        env.rate.execute(drawn(env, interpret=False), USER, 50)
