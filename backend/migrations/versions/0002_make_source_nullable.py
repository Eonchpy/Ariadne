"""make source_id nullable on tables

Revision ID: 0002_make_source_nullable
Revises: 0001_initial
Create Date: 2025-12-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_make_source_nullable"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tables", "source_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("tables", "source_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
