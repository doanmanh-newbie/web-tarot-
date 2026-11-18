"""enable row level security on all tables

Supabase tự mở schema public qua REST API bằng anon key. Bật RLS mà không tạo policy nào
thì anon/authenticated không đọc ghi được gì; backend kết nối bằng chủ bảng (postgres) nên
không bị ảnh hưởng. Trên Postgres thường (Docker local) lệnh này vô hại.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-18
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

TABLES = ("users", "cards", "spreads", "spread_positions", "readings", "reading_cards", "alembic_version")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
