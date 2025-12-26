"""add unique constraint on (source_id, name) for tables

Revision ID: 0006_unique_table_source_name
Revises: 0005_add_primary_tag_id
Create Date: 2025-12-26
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_unique_table_source_name"
down_revision = "0005_primary_tag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ux_tables_source_name",
        "tables",
        ["source_id", "name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_tables_source_name", table_name="tables")
