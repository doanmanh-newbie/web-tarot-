"""Chống lách giới hạn lượt bằng cách bấm đồng thời, kiểm chứng trên PostgreSQL THẬT.

SQLite không đủ để kiểm chứng việc này (cách nó khóa dữ liệu khác Postgres), nên test này chỉ chạy khi có
biến môi trường TEST_POSTGRES_URL, ví dụ:
    TEST_POSTGRES_URL=postgresql+psycopg://tarot:tarot@localhost:5432/tarot_test pytest tests/integration

LƯU Ý: test xóa toàn bộ bảng trong DB đó (drop_all), chỉ trỏ vào DB dành riêng cho test.
Khi đã đo thử: bỏ khóa advisory thì 12 request đồng thời với limit=3 đều lọt qua (12 lượt); có khóa thì luôn đúng 3.
"""
import os
import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.modules.auth.infrastructure import models as _auth  # noqa: F401
from app.modules.auth.infrastructure.models import UserModel
from app.modules.cards.infrastructure import models as _cards  # noqa: F401
from app.modules.readings.domain.reading import DrawnCard, Reading
from app.modules.readings.infrastructure.models import ReadingModel
from app.modules.readings.infrastructure.sqlalchemy_reading_repository import SqlAlchemyReadingRepository
from app.modules.spreads.infrastructure import models as _spreads  # noqa: F401
from app.shared.infrastructure.db.base import Base
from scripts.seed_cards import load_data, seed_database

URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="cần TEST_POSTGRES_URL (PostgreSQL thật)")


@pytest.fixture
def pg():
    engine = create_engine(URL, pool_size=30)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    cards, spreads = load_data()
    with factory() as s:
        seed_database(s, cards, spreads)
        s.add_all([UserModel(email=f"u{i}@example.com", password_hash="x", role="user") for i in (1, 2)])
        s.commit()
    yield factory
    engine.dispose()
    clean = create_engine(URL)
    Base.metadata.drop_all(clean)
    clean.dispose()


def _hammer(factory, user_id, workers, limit):
    now = datetime.now(timezone.utc)
    window = (now - timedelta(hours=1), now + timedelta(hours=1))
    barrier = threading.Barrier(workers)
    saved = []

    def worker():
        with factory() as session:
            reading = Reading(
                id=None, user_id=user_id, spread_id=1, question="q",
                drawn_cards=[DrawnCard(1, 0, False)], created_at=now,
            )
            barrier.wait()  # cho tất cả cùng xuất phát một lúc
            saved.append(SqlAlchemyReadingRepository(session).add_if_under_limit(reading, limit, *window) is not None)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(saved)


def _count(factory, user_id):
    with factory() as s:
        return s.scalar(select(func.count()).select_from(ReadingModel).where(ReadingModel.user_id == user_id))


@pytest.mark.parametrize("round_", range(3))
def test_concurrent_draws_never_exceed_the_limit(pg, round_):
    assert _hammer(pg, user_id=1, workers=12, limit=3) == 3
    assert _count(pg, 1) == 3


def test_concurrent_draws_of_different_users_do_not_block_each_other(pg):
    results = {}

    def run(uid):
        results[uid] = _hammer(pg, user_id=uid, workers=8, limit=3)

    threads = [threading.Thread(target=run, args=(uid,)) for uid in (1, 2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == {1: 3, 2: 3}
