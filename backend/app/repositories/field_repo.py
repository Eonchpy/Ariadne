from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field import MetadataField
from app.repositories.base import BaseRepository


class FieldRepository(BaseRepository[MetadataField]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MetadataField)

    async def list_by_table(self, table_id: str) -> Sequence[MetadataField]:
        result = await self.session.execute(
            select(MetadataField).where(MetadataField.table_id == table_id)
        )
        return result.scalars().all()
