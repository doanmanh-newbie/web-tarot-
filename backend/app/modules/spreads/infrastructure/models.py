from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.db.base import Base


class SpreadModel(Base):
    __tablename__ = "spreads"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")

    positions: Mapped[list["SpreadPositionModel"]] = relationship(
        back_populates="spread",
        cascade="all, delete-orphan",
        order_by="SpreadPositionModel.position_index",
    )


class SpreadPositionModel(Base):
    __tablename__ = "spread_positions"
    __table_args__ = (UniqueConstraint("spread_id", "position_index", name="uq_spread_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    spread_id: Mapped[int] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"))
    position_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")

    spread: Mapped[SpreadModel] = relationship(back_populates="positions")
