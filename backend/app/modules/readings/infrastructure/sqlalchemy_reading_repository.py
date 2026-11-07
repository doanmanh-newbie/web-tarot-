from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.modules.quota.application.ports.reading_counter import ReadingCounter
from app.modules.readings.domain.exceptions import ReadingNotFound
from app.modules.readings.domain.reading import AIStatus, DrawnCard, Reading
from app.modules.readings.domain.reading_repository import ReadingRepository
from app.modules.readings.infrastructure.models import ReadingCardModel, ReadingModel

# Khóa advisory của Postgres: (namespace, user_id). Namespace tùy ý, miễn không trùng chỗ khác trong app.
_LOCK_NAMESPACE = 7001


def _utc(value: datetime) -> datetime:
    """Chuẩn hóa về UTC. SQLite trả datetime không có tzinfo, coi đó là UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_entity(m: ReadingModel) -> Reading:
    return Reading(
        id=m.id,
        user_id=m.user_id,
        spread_id=m.spread_id,
        question=m.question,
        drawn_cards=[DrawnCard(c.card_id, c.position_index, c.is_reversed) for c in m.cards],
        ai_interpretation=m.ai_interpretation,
        ai_status=AIStatus(m.ai_status),
        created_at=_utc(m.created_at),
    )


class SqlAlchemyReadingRepository(ReadingRepository, ReadingCounter):
    """Cài đặt ReadingRepository (module readings) và ReadingCounter (port của module quota)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---- quota ----------------------------------------------------------------------------
    def count_by_user_between(self, user_id: int, start: datetime, end: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(ReadingModel)
            .where(
                ReadingModel.user_id == user_id,
                ReadingModel.created_at >= _utc(start),
                ReadingModel.created_at < _utc(end),
            )
        )
        # Cố ý KHÔNG lọc deleted_at: reading đã xóa vẫn tính vào quota.
        return int(self._session.scalar(stmt) or 0)

    def add_if_under_limit(
        self, reading: Reading, limit: int | None, window_start: datetime, window_end: datetime
    ) -> Reading | None:
        if self._session.get_bind().dialect.name == "postgresql":
            # Khóa theo user đến hết transaction: hai request cùng user phải xếp hàng,
            # request sau sẽ đếm thấy lượt của request trước. Khóa tự nhả khi commit/rollback.
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(:ns, :uid)"), {"ns": _LOCK_NAMESPACE, "uid": reading.user_id}
            )
        if limit is not None:
            used = self.count_by_user_between(reading.user_id, window_start, window_end)
            if used >= limit:
                self._session.rollback()  # nhả khóa
                return None

        model = ReadingModel(
            user_id=reading.user_id,
            spread_id=reading.spread_id,
            question=reading.question,
            ai_status=AIStatus.PENDING.value,
            created_at=_utc(reading.created_at),
            cards=[
                ReadingCardModel(card_id=c.card_id, position_index=c.position_index, is_reversed=c.is_reversed)
                for c in reading.drawn_cards
            ],
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    # ---- đọc / ghi thường -----------------------------------------------------------------
    def get_by_id(self, reading_id: int) -> Reading | None:
        stmt = (
            select(ReadingModel)
            .where(ReadingModel.id == reading_id, ReadingModel.deleted_at.is_(None))
            .options(selectinload(ReadingModel.cards))
        )
        model = self._session.scalars(stmt).first()
        return _to_entity(model) if model else None

    def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> list[Reading]:
        stmt = (
            select(ReadingModel)
            .where(ReadingModel.user_id == user_id, ReadingModel.deleted_at.is_(None))
            .options(selectinload(ReadingModel.cards))
            .order_by(ReadingModel.created_at.desc(), ReadingModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(m) for m in self._session.scalars(stmt).all()]

    def update_interpretation(self, reading_id: int, text: str | None, status: AIStatus) -> Reading:
        model = self._session.get(ReadingModel, reading_id)
        if model is None:
            raise ReadingNotFound(str(reading_id))
        model.ai_interpretation = text
        model.ai_status = status.value
        self._session.commit()
        return _to_entity(model)

    def delete(self, reading_id: int) -> None:
        model = self._session.get(ReadingModel, reading_id)
        if model is None:
            raise ReadingNotFound(str(reading_id))
        model.deleted_at = datetime.now(timezone.utc)
        self._session.commit()
