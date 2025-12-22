import uuid
from datetime import datetime, timezone
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import DataSource
from app.repositories.source_repo import SourceRepository
from app.schemas.source import Source, SourceCreate, SourceUpdate


class SourceService:
    """PostgreSQL-backed source service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SourceRepository(session)

    async def list_sources(self, page: int = 1, size: int = 20) -> Tuple[list[Source], int]:
        items, total = await self.repo.paginate(page=page, size=size)
        return [self._to_schema(item) for item in items], total

    async def create_source(self, payload: SourceCreate) -> Source:
        source = DataSource(
            id=uuid.uuid4(),
            name=payload.name,
            type=payload.type,
            description=payload.description,
            connection_config=payload.connection_config,
            is_active=True,
        )
        await self.repo.add(source)
        await self.session.commit()
        return self._to_schema(source)

    async def get_source(self, source_id: str) -> Source:
        source = await self.repo.get(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        return self._to_schema(source)

    async def update_source(self, source_id: str, payload: SourceUpdate) -> Source:
        source = await self.repo.get(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(source, key, value)
        await self.session.commit()
        await self.session.refresh(source)
        return self._to_schema(source)

    async def delete_source(self, source_id: str) -> None:
        source = await self.repo.get(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        await self.repo.delete(source)
        await self.session.commit()

    @staticmethod
    def _to_schema(source: DataSource) -> Source:
        return Source.model_validate(source, from_attributes=True)
