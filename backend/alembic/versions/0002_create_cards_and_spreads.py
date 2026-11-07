"""create cards, spreads, spread_positions

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_vi", sa.String(100), nullable=False),
        sa.Column("arcana", sa.String(10), nullable=False),
        sa.Column("suit", sa.String(20), nullable=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("upright_meaning", sa.Text(), nullable=False),
        sa.Column("reversed_meaning", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(255), nullable=True),
        sa.CheckConstraint("arcana in ('major', 'minor')", name="ck_cards_arcana"),
    )
    op.create_index("ix_cards_slug", "cards", ["slug"], unique=True)

    op.create_table(
        "spreads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_spreads_slug", "spreads", ["slug"], unique=True)

    op.create_table(
        "spread_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spread_id", sa.Integer(), sa.ForeignKey("spreads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("spread_id", "position_index", name="uq_spread_position"),
    )


def downgrade() -> None:
    op.drop_table("spread_positions")
    op.drop_index("ix_spreads_slug", table_name="spreads")
    op.drop_table("spreads")
    op.drop_index("ix_cards_slug", table_name="cards")
    op.drop_table("cards")
