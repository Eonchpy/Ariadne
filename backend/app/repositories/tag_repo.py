import uuid
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, TableTag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Tag)

    async def list_by_filters(self, level: Optional[int] = None, parent_id: Optional[uuid.UUID] = None) -> Sequence[Tag]:
        query = select(Tag)
        if level is not None:
            query = query.where(Tag.level == level)
        if parent_id is not None:
            query = query.where(Tag.parent_id == parent_id)
        result = await self.session.execute(query.order_by(Tag.path.asc()))
        return result.scalars().all()

    async def get_descendants_ids(self, tag_ids: List[uuid.UUID]) -> List[uuid.UUID]:
        if not tag_ids:
            return []
        cte = select(Tag.id, Tag.parent_id).cte(name="tag_tree", recursive=True)
        cte = cte.union_all(select(Tag.id, Tag.parent_id).where(Tag.parent_id == cte.c.id))
        result = await self.session.execute(select(cte.c.id).where(cte.c.id.in_(tag_ids)))
        return [row[0] for row in result.all()]

    async def add_table_tags(self, table_id: uuid.UUID, tag_ids: List[uuid.UUID]) -> None:
        if not tag_ids:
            return
        stmt = insert(TableTag).values([{"table_id": table_id, "tag_id": tag_id} for tag_id in tag_ids])
        stmt = stmt.on_conflict_do_nothing(index_elements=[TableTag.table_id, TableTag.tag_id])
        await self.session.execute(stmt)

    async def remove_all_tags_for_table(self, table_id: uuid.UUID) -> None:
        await self.session.execute(TableTag.__table__.delete().where(TableTag.table_id == table_id))

    async def remove_table_tag(self, table_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        await self.session.execute(
            TableTag.__table__.delete().where(
                and_(TableTag.table_id == table_id, TableTag.tag_id == tag_id)
            )
        )

    async def list_table_tags(self, table_id: uuid.UUID) -> Sequence[Tag]:
        result = await self.session.execute(
            select(Tag)
            .join(TableTag, TableTag.tag_id == Tag.id)
            .where(TableTag.table_id == table_id)
            .order_by(Tag.path.asc())
        )
        return result.scalars().all()

    async def tag_usage(self, tag_id: uuid.UUID):
        tables_query = (
            select(TableTag.table_id, func.count().over())
            .where(TableTag.tag_id == tag_id)
        )
        result = await self.session.execute(tables_query)
        rows = result.fetchall()
        ids = [r[0] for r in rows]
        total = rows[0][1] if rows else 0
        return total, ids
