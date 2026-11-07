from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CardModel(Base):
    __tablename__ = "cards"
    __table_args__ = (CheckConstraint("arcana in ('major', 'minor')", name="ck_cards_arcana"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    name_vi: Mapped[str] = mapped_column(String(100))
    arcana: Mapped[str] = mapped_column(String(10))
    suit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    number: Mapped[int] = mapped_column(Integer)
    upright_meaning: Mapped[str] = mapped_column(Text)
    reversed_meaning: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
