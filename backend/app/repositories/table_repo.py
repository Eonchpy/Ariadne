from typing import Sequence
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import MetadataTable
from app.repositories.base import BaseRepository


class TableRepository(BaseRepository[MetadataTable]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetadataTable)

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
