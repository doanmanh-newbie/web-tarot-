from datetime import timedelta

import pytest

from app.modules.quota.domain.exceptions import DailyQuotaExceeded
from app.modules.readings.domain.exceptions import ReadingNotFound
from tests.unit.modules.readings.fakes import make_env

USER, OTHER = 1, 2


def test_list_is_newest_first_and_only_mine():
    env = make_env(limit=10)
    ids = []
    for _ in range(3):
        ids.append(env.draw.execute(USER, 1, "q").reading.id)
        env.clock.at += timedelta(minutes=1)
    env.draw.execute(OTHER, 1, "của người khác")
    assert [d.reading.id for d in env.list.execute(USER)] == ids[::-1]


def test_list_pagination():
    env = make_env(limit=10)
    for _ in range(5):
        env.draw.execute(USER, 1, "q")
        env.clock.at += timedelta(minutes=1)
    assert len(env.list.execute(USER, limit=2, offset=0)) == 2
    assert len(env.list.execute(USER, limit=2, offset=4)) == 1


def test_list_empty_for_new_user():
    assert make_env().list.execute(USER) == []


def test_get_own_reading_includes_card_details():
    env = make_env()
    rid = env.draw.execute(USER, 1, "q").reading.id
    details = env.get.execute(rid, USER)
    assert details.cards[0].card.name == "Card 1" and details.spread.name == "Spread 1"


def test_get_other_users_reading_is_not_found():
    env = make_env()
    rid = env.draw.execute(USER, 1, "q").reading.id
    with pytest.raises(ReadingNotFound):
        env.get.execute(rid, OTHER)


def test_delete_hides_reading_from_history():
    env = make_env()
    rid = env.draw.execute(USER, 1, "q").reading.id
    env.delete.execute(rid, USER)
    assert env.list.execute(USER) == []
    with pytest.raises(ReadingNotFound):
        env.get.execute(rid, USER)


def test_deleting_history_does_not_refund_quota():
    env = make_env(limit=3)
    ids = [env.draw.execute(USER, 1, "q").reading.id for _ in range(3)]
    for rid in ids:
        env.delete.execute(rid, USER)
    with pytest.raises(DailyQuotaExceeded):
        env.draw.execute(USER, 1, "q")
    assert env.quota.execute(USER).used == 3


def test_cannot_delete_someone_elses_reading():
    env = make_env()
    rid = env.draw.execute(USER, 1, "q").reading.id
    with pytest.raises(ReadingNotFound):
        env.delete.execute(rid, OTHER)
    assert len(env.list.execute(USER)) == 1
