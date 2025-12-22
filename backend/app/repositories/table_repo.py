from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import MetadataTable
from app.repositories.base import BaseRepository


class TableRepository(BaseRepository[MetadataTable]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetadataTable)

    async def paginate(self, page: int, size: int) -> tuple[Sequence[MetadataTable], int]:
        total_result = await self.session.execute(select(func.count()).select_from(MetadataTable))
        total = total_result.scalar_one()
        result = await self.session.execute(
            select(MetadataTable)
            .offset((page - 1) * size)
            .limit(size)
            .order_by(MetadataTable.created_at.desc())
        )
        return result.scalars().all(), total
