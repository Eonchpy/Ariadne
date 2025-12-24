"""add tags tables

Revision ID: 0004_add_tags
Revises: 0003_add_connection_test_logs
Create Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_add_tags"
down_revision = "0003_add_connection_test_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["tags.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("level BETWEEN 1 AND 3"),
        sa.UniqueConstraint("path", name="unique_tag_path"),
    )
    op.create_index("idx_tags_parent", "tags", ["parent_id"])
    op.create_index("idx_tags_path", "tags", ["path"])
    op.create_index("idx_tags_level", "tags", ["level"])

    op.create_table(
        "table_tags",
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("table_id", "tag_id"),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_table_tags_table", "table_tags", ["table_id"])
    op.create_index("idx_table_tags_tag", "table_tags", ["tag_id"])


def downgrade():
    op.drop_index("idx_table_tags_tag", table_name="table_tags")
    op.drop_index("idx_table_tags_table", table_name="table_tags")
    op.drop_table("table_tags")
    op.drop_index("idx_tags_level", table_name="tags")
    op.drop_index("idx_tags_path", table_name="tags")
    op.drop_index("idx_tags_parent", table_name="tags")
    op.drop_table("tags")
