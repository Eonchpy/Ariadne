"""stub for primary_tag revision to align with existing DB state

Revision ID: 0005_primary_tag
Revises: 0004_add_tags
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_primary_tag"
down_revision = "0004_add_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure primary_tag_id column exists; if already present, ignore.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("tables")]
    if "primary_tag_id" not in cols:
        op.add_column(
            "tables",
            sa.Column(
                "primary_tag_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tags.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    # If column exists, no further action needed.


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("tables")]
    if "primary_tag_id" in cols:
        op.drop_column("tables", "primary_tag_id")

