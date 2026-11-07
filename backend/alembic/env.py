"""Alembic env. Mỗi module thêm một dòng import models vào đây."""
from sqlalchemy import create_engine

from alembic import context
from app.config import get_settings
from app.modules.auth.infrastructure import models as auth_models  # noqa: F401
from app.modules.cards.infrastructure import models as cards_models  # noqa: F401
from app.modules.readings.infrastructure import models as readings_models  # noqa: F401
from app.modules.spreads.infrastructure import models as spreads_models  # noqa: F401
from app.shared.infrastructure.db.base import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
