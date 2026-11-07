from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.modules.auth.application.use_cases.register_user import RegisterUser
from app.modules.auth.domain.user import Role
from app.modules.auth.infrastructure import models as _auth_models  # noqa: F401
from app.modules.auth.infrastructure.bcrypt_hasher import BcryptHasher
from app.modules.auth.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.modules.auth.presentation.dependencies import get_password_hasher
from app.modules.cards.infrastructure import models as _cards_models  # noqa: F401
from app.modules.readings.infrastructure import models as _readings_models  # noqa: F401
from app.modules.readings.presentation.dependencies import get_ai_interpreter
from app.modules.spreads.infrastructure import models as _spreads_models  # noqa: F401
from app.shared.application.ports.clock import Clock
from app.shared.infrastructure.db.base import Base
from app.shared.presentation.dependencies import get_clock, get_db_session
from scripts.seed_cards import load_data, seed_database
from tests.unit.modules.readings.fakes import FakeAI


class ClockOverride(Clock):
    """Mặc định chạy theo giờ thật; test đặt `.at` để giả lập thời điểm khác (vd sang ngày mới)."""

    def __init__(self) -> None:
        self.at: datetime | None = None

    def now(self) -> datetime:
        return self.at or datetime.now(timezone.utc)


@pytest.fixture
def ctx():
    """App thật + SQLite in-memory + bcrypt rounds thấp + AI giả (không gọi Gemini) + đồng hồ chỉnh được."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    hasher = BcryptHasher(rounds=4)
    ai = FakeAI()
    clock = ClockOverride()

    def override_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_password_hasher] = lambda: hasher
    app.dependency_overrides[get_ai_interpreter] = lambda: ai
    app.dependency_overrides[get_clock] = lambda: clock
    client = TestClient(app)

    def make_user(email, password="matkhau123", role=Role.USER):
        with session_factory() as session:
            return RegisterUser(SqlAlchemyUserRepository(session), hasher).execute(email, password, role=role)

    def login(email, password="matkhau123"):
        res = TestClient(app).post("/auth/login", json={"email": email, "password": password})
        return res.json()["access_token"]

    def auth_header(role=Role.USER, email=None):
        """Tạo user rồi trả header Authorization. Truyền `email` khác nhau để có nhiều user."""
        email = email or f"{role.value}@example.com"
        make_user(email, role=role)
        return {"Authorization": f"Bearer {login(email)}"}

    def seed():
        cards, spreads = load_data()
        with session_factory() as session:
            return seed_database(session, cards, spreads)

    yield SimpleNamespace(
        app=app,
        client=client,
        ai=ai,
        clock=clock,
        make_user=make_user,
        login=login,
        auth_header=auth_header,
        seed=seed,
        session_factory=session_factory,
    )
    engine.dispose()
