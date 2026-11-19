"""add readings.accuracy (người dùng tự chấm lời giải đúng bao nhiêu %, 0-100)

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19
"""
import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("readings", sa.Column("accuracy", sa.SmallInteger(), nullable=True))
    op.create_check_constraint("ck_readings_accuracy_range", "readings", "accuracy BETWEEN 0 AND 100")


def downgrade() -> None:
    op.drop_constraint("ck_readings_accuracy_range", "readings", type_="check")
    op.drop_column("readings", "accuracy")
