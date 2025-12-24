from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.audit import ConnectionTestLog
from app.repositories.base import BaseRepository


class ConnectionTestLogRepository(BaseRepository[ConnectionTestLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ConnectionTestLog)

    async def list_by_source(self, source_id: str | None = None, limit: int = 100) -> Sequence[ConnectionTestLog]:
        stmt = select(ConnectionTestLog).order_by(ConnectionTestLog.created_at.desc()).limit(limit)
        if source_id:
            stmt = stmt.where(ConnectionTestLog.source_id == source_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
