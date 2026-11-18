"""add cards.details (nội dung mở rộng của lá bài, dạng JSON)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("details", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "details")
