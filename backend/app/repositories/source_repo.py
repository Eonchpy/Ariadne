from typing import Optional, Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import DataSource
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[DataSource]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DataSource)

    async def paginate(self, page: int, size: int) -> tuple[Sequence[DataSource], int]:
        total_result = await self.session.execute(select(func.count()).select_from(DataSource))
        total = total_result.scalar_one()
        result = await self.session.execute(
            select(DataSource).offset((page - 1) * size).limit(size).order_by(DataSource.created_at.desc())
        )
        return result.scalars().all(), total
