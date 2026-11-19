"""add readings.prompt_version (phiên bản prompt sinh lời giải, để so độ đúng trước/sau khi sửa prompt)

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-19
"""
import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("readings", sa.Column("prompt_version", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("readings", "prompt_version")
