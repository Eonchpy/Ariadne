import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field import MetadataField
from app.repositories.field_repo import FieldRepository
from app.schemas.field import Field, FieldCreate, FieldUpdate, FieldCreateInTable
from app.services.lineage_service import LineageService


class FieldService:
    """PostgreSQL-backed field service."""

    def __init__(self, session: AsyncSession, lineage_driver=None):
        self.session = session
        self.repo = FieldRepository(session)
        self.lineage_driver = lineage_driver

    async def list_fields_for_table(self, table_id: str) -> List[Field]:
        fields = await self.repo.list_by_table(table_id)
        return [self._to_schema(f) for f in fields]

    async def create_field(self, payload: FieldCreate | FieldCreateInTable, table_id: str | None = None) -> Field:
        table_id_value = table_id or getattr(payload, "table_id", None)
        if not table_id_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="table_id is required")
        field = MetadataField(
            id=uuid.uuid4(),
            table_id=table_id_value,
            name=payload.name,
            data_type=payload.data_type,
            description=payload.description,
            is_nullable=payload.is_nullable,
            is_primary_key=payload.is_primary_key,
            is_foreign_key=payload.is_foreign_key,
        )
        await self.repo.add(field)
        await self.session.commit()
        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_field_node(
                {
                    "id": str(field.id),
                    "name": field.name,
                    "data_type": field.data_type,
                    "table_id": str(field.table_id),
                }
            )
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
        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_field_node(
                {
                    "id": str(field.id),
                    "name": field.name,
                    "data_type": field.data_type,
                    "table_id": str(field.table_id),
                }
            )
        return self._to_schema(field)

    async def delete_field(self, field_id: str) -> None:
        field = await self.repo.get(field_id)
        if not field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
        await self.repo.delete(field)
        await self.session.commit()
        if self.lineage_driver:
            await LineageService(self.lineage_driver).delete_field_node(str(field.id))

    async def create_fields_batch(self, table_id: str, payloads: List[FieldCreate | FieldCreateInTable]) -> List[Field]:
        created: list[Field] = []
        async with self.session.begin():
            for payload in payloads:
                field = MetadataField(
                    id=uuid.uuid4(),
                    table_id=table_id,
                    name=payload.name,
                    data_type=payload.data_type,
                    description=getattr(payload, "description", None),
                    is_nullable=getattr(payload, "is_nullable", None),
                    is_primary_key=getattr(payload, "is_primary_key", None),
                    is_foreign_key=getattr(payload, "is_foreign_key", None),
                )
                await self.repo.add(field)
                created.append(self._to_schema(field))
        if self.lineage_driver:
            svc = LineageService(self.lineage_driver)
            for f in created:
                await svc.sync_field_node(
                    {"id": str(f.id), "name": f.name, "data_type": f.data_type, "table_id": str(f.table_id)}
                )
        return created

    @staticmethod
    def _to_schema(field: MetadataField) -> Field:
        return Field.model_validate(field, from_attributes=True)
