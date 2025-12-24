"""add connection_test_logs

Revision ID: 0003_add_connection_test_logs
Revises: 0002_make_source_nullable
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_add_connection_test_logs"
down_revision = "0002_make_source_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connection_test_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE")),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("table_name", sa.String(length=255), nullable=True),
        sa.Column("tested_by", sa.String(length=100), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("connection_test_logs")
