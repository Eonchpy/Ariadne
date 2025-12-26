"""add name_normalized and unique index on (source_id, name_normalized)

Revision ID: 0007_add_name_normalized_unique
Revises: 0006_unique_table_source_name
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_add_name_normalized_unique"
down_revision = "0006_unique_table_source_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add column (temporarily nullable), backfill, then set NOT NULL
    op.add_column("tables", sa.Column("name_normalized", sa.String(length=255), nullable=True))
    op.execute("UPDATE tables SET name_normalized = lower(name)")
    op.alter_column("tables", "name_normalized", nullable=False)

    # drop old unique index if present
    op.execute("DROP INDEX IF EXISTS ux_tables_source_name")
    # create new unique index on normalized name
    op.create_index(
        "ux_tables_source_norm",
        "tables",
        ["source_id", "name_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_tables_source_norm", table_name="tables")
    op.drop_column("tables", "name_normalized")
    # optionally recreate old index
    op.create_index("ux_tables_source_name", "tables", ["source_id", "name"], unique=True)
