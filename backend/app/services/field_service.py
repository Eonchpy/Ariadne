import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field import MetadataField
from app.repositories.field_repo import FieldRepository
from app.schemas.field import Field, FieldCreate, FieldUpdate


class FieldService:
    """PostgreSQL-backed field service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FieldRepository(session)

    async def list_fields_for_table(self, table_id: str) -> List[Field]:
        fields = await self.repo.list_by_table(table_id)
        return [self._to_schema(f) for f in fields]

    async def create_field(self, payload: FieldCreate) -> Field:
        field = MetadataField(
            id=uuid.uuid4(),
            table_id=payload.table_id,
            name=payload.name,
            data_type=payload.data_type,
            description=payload.description,
            is_nullable=payload.is_nullable,
            is_primary_key=payload.is_primary_key,
            is_foreign_key=payload.is_foreign_key,
        )
        await self.repo.add(field)
        await self.session.commit()
        return self._to_schema(field)

    async def get_field(self, field_id: str) -> Field:
        field = await self.repo.get(field_id)
        if not field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
        return self._to_schema(field)

    async def update_field(self, field_id: str, payload: FieldUpdate) -> Field:
        field = await self.repo.get(field_id)
        if not field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(field, key, value)
        await self.session.commit()
        await self.session.refresh(field)
        return self._to_schema(field)

    async def delete_field(self, field_id: str) -> None:
        field = await self.repo.get(field_id)
        if not field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
        await self.repo.delete(field)
        await self.session.commit()

    @staticmethod
    def _to_schema(field: MetadataField) -> Field:
        return Field.model_validate(field, from_attributes=True)
