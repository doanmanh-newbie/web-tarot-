"""create readings, reading_cards

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spread_id", sa.Integer(), sa.ForeignKey("spreads.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("ai_interpretation", sa.Text(), nullable=True),
        sa.Column("ai_status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_readings_user_created", "readings", ["user_id", "created_at"])

    op.create_table(
        "reading_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reading_id", sa.Integer(), sa.ForeignKey("readings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("is_reversed", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("reading_id", "position_index", name="uq_reading_card_position"),
    )


def downgrade() -> None:
    op.drop_table("reading_cards")
    op.drop_index("ix_readings_user_created", table_name="readings")
    op.drop_table("readings")
