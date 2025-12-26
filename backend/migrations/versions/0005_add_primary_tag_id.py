"""add primary_tag_id to tables

Revision ID: 0005_add_primary_tag_id
Revises: 0004_add_tags
Create Date: 2025-12-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_add_primary_tag_id"
down_revision = "0004_add_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tables",
        sa.Column("primary_tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("idx_tables_primary_tag", "tables", ["primary_tag_id"])


def downgrade() -> None:
    op.drop_index("idx_tables_primary_tag", table_name="tables")
    op.drop_column("tables", "primary_tag_id")

