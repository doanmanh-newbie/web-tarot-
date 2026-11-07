"""Dependency dùng chung cho router: session DB, clock, settings."""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.shared.infrastructure.db.session import SessionLocal
from app.shared.infrastructure.system_clock import SystemClock


def get_db_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_clock() -> SystemClock:
    return SystemClock()
