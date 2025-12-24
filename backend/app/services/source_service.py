import uuid
from datetime import datetime, timezone
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import DataSource
from app.repositories.source_repo import SourceRepository
from app.schemas.source import Source, SourceCreate, SourceUpdate
from app.core.encryption import encrypt_dict, decrypt_dict, mask_dict
from app.services.connection_service import ConnectionService
from app.repositories.audit_repo import ConnectionTestLogRepository


class SourceService:
    """PostgreSQL-backed source service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SourceRepository(session)
        self.audit_repo = ConnectionTestLogRepository(session)

    async def list_sources(self, page: int = 1, size: int = 20) -> Tuple[list[Source], int]:
        items, total = await self.repo.paginate(page=page, size=size)
        return [self._to_schema(item) for item in items], total

    async def create_source(self, payload: SourceCreate, tag_service=None) -> Source:
        source = DataSource(
            id=uuid.uuid4(),
            name=payload.name,
            type=payload.type,
            description=payload.description,
            connection_config=encrypt_dict(payload.connection_config or {}),
            is_active=True,
        )
        await self.repo.add(source)
        await self.session.commit()
        if tag_service:
            root = await tag_service.get_or_create_tag(name="DataSource", level=1, parent_id=None)
            type_tag = await tag_service.get_or_create_tag(name=source.type, level=2, parent_id=root.id)
            await tag_service.get_or_create_tag(name=source.name, level=3, parent_id=type_tag.id)
        return self._to_schema(source)

    async def get_source(self, source_id: str) -> Source:
        source = await self._get_entity(source_id)
        return self._to_schema(source)

    async def update_source(self, source_id: str, payload: SourceUpdate) -> Source:
        source = await self.repo.get(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(source, key, value)
        if payload.connection_config is not None:
            source.connection_config = encrypt_dict(payload.connection_config or {})
        await self.session.commit()
        await self.session.refresh(source)
        return self._to_schema(source)

    async def delete_source(self, source_id: str) -> None:
        source = await self._get_entity(source_id)
        await self.repo.delete(source)
        await self.session.commit()

    async def test_connection(self, source_id: str):
        source = await self._get_entity(source_id)
        service = ConnectionService(
            source_type=source.type,
            connection_config=source.connection_config or {},
            audit_repo=self.audit_repo,
        )
        return await service.test_connection(source_id=str(source.id), tested_by=None)

    async def _get_entity(self, source_id: str) -> DataSource:
        source = await self.repo.get(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        return source

    @staticmethod
    def _to_schema(source: DataSource) -> Source:
        config = decrypt_dict(source.connection_config or {})
        masked = mask_dict(config)
        return Source(
            id=str(source.id),
            name=source.name,
            type=source.type,
            description=source.description,
            connection_config=masked,
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
