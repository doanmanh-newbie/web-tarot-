from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.db.base import Base


class ReadingModel(Base):
    __tablename__ = "readings"
    __table_args__ = (Index("ix_readings_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    spread_id: Mapped[int] = mapped_column(ForeignKey("spreads.id"))
    question: Mapped[str] = mapped_column(Text)
    ai_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(10), default="pending", server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cards: Mapped[list["ReadingCardModel"]] = relationship(
        back_populates="reading",
        cascade="all, delete-orphan",
        order_by="ReadingCardModel.position_index",
    )


class ReadingCardModel(Base):
    __tablename__ = "reading_cards"
    __table_args__ = (UniqueConstraint("reading_id", "position_index", name="uq_reading_card_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reading_id: Mapped[int] = mapped_column(ForeignKey("readings.id", ondelete="CASCADE"))
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))
    position_index: Mapped[int] = mapped_column(Integer)
    is_reversed: Mapped[bool] = mapped_column(Boolean)

    reading: Mapped[ReadingModel] = relationship(back_populates="cards")
