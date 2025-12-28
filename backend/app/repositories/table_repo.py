from typing import Sequence
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import MetadataTable
from app.repositories.base import BaseRepository


class TableRepository(BaseRepository[MetadataTable]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetadataTable)

    async def search_by_name(self, keyword: str, limit: int = 20):
        """Search tables by name (case-insensitive, contains)."""
        pattern = f"%{keyword}%"
        stmt = select(MetadataTable).where(MetadataTable.name.ilike(pattern)).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_by_name_exact(self, name: str):
        stmt = select(MetadataTable).where(MetadataTable.name == name)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_by_name_normalized(self, name: str):
        """Case-insensitive exact match using name_normalized."""
        normalized = name.lower()
        stmt = select(MetadataTable).where(MetadataTable.name_normalized == normalized)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_tables_with_primary_tags(self, table_ids: list[uuid.UUID]) -> dict[str, dict]:
        """Return mapping of table_id -> {primary_tag, primary_tag_id, source_name, source_id, name}."""
        if not table_ids:
            return {}

        from app.models.tag import Tag  # local import to avoid circular
        from app.models.source import DataSource

        stmt = (
            select(
                MetadataTable.id,
                MetadataTable.name,
                MetadataTable.primary_tag_id,
                MetadataTable.source_id,
                Tag.id,
                Tag.name,
                Tag.path,
                Tag.level,
                DataSource.name,
            )
            .outerjoin(Tag, MetadataTable.primary_tag_id == Tag.id)
            .outerjoin(DataSource, MetadataTable.source_id == DataSource.id)
            .where(MetadataTable.id.in_(table_ids))
        )
        result = await self.session.execute(stmt)
        mapping: dict[str, dict] = {}
        for (
            table_id,
            table_name,
            primary_tag_id,
            source_id,
            tag_id,
            tag_name,
            tag_path,
            tag_level,
            source_name,
        ) in result.all():
            primary_tag = None
            if tag_id:
                primary_tag = {
                    "id": str(tag_id),
                    "name": tag_name,
                    "path": tag_path,
                    "level": tag_level,
                }
            mapping[str(table_id)] = {
                "id": str(table_id),
                "name": table_name,
                "primary_tag_id": str(primary_tag_id) if primary_tag_id else None,
                "primary_tag": primary_tag,
                "source_id": str(source_id) if source_id else None,
                "source_name": source_name,
            }
        return mapping

    async def paginate(
        self,
        page: int,
        size: int,
        search: str | None = None,
        source_id: str | None = None,
        tag_ids: list[str] | None = None,
        tag_match: str | None = "any",
        include_subtags: bool = False,
    ) -> tuple[Sequence[MetadataTable], int]:
        query = select(MetadataTable)
        count_query = select(func.count()).select_from(MetadataTable)

        if search:
            pattern = f"%{search}%"
            query = query.where(MetadataTable.name.ilike(pattern))
            count_query = count_query.where(MetadataTable.name.ilike(pattern))

        if source_id:
            query = query.where(MetadataTable.source_id == source_id)
            count_query = count_query.where(MetadataTable.source_id == source_id)

        if tag_ids:
            from app.models.tag import TableTag, Tag  # local import to avoid cycles

            tag_uuid = [uuid.UUID(t) for t in tag_ids]
            target_tags = tag_uuid
            if include_subtags:
                cte = select(Tag.id, Tag.parent_id).where(Tag.id.in_(tag_uuid)).cte(
                    name="tag_tree", recursive=True
                )
                cte = cte.union_all(select(Tag.id, Tag.parent_id).where(Tag.parent_id == cte.c.id))
                result = await self.session.execute(select(cte.c.id))
                target_tags = [row[0] for row in result.all()]

            tt = select(TableTag.table_id).where(TableTag.tag_id.in_(target_tags))
            if tag_match == "all":
                tt = tt.group_by(TableTag.table_id).having(func.count() >= len(target_tags))
            tag_filter_table_ids = select(tt.c.table_id) if hasattr(tt, "c") else tt
            query = query.where(MetadataTable.id.in_(tag_filter_table_ids))
            count_query = count_query.where(MetadataTable.id.in_(tag_filter_table_ids))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        result = await self.session.execute(
            query.offset((page - 1) * size).limit(size).order_by(MetadataTable.created_at.desc())
        )
        return result.scalars().all(), total
