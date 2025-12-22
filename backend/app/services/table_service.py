import uuid
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import MetadataTable
from app.repositories.table_repo import TableRepository
from app.schemas.table import Table, TableCreate, TableUpdate


class TableService:
    """PostgreSQL-backed table service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TableRepository(session)

    async def list_tables(self, page: int = 1, size: int = 20) -> Tuple[list[Table], int]:
        items, total = await self.repo.paginate(page=page, size=size)
        return [self._to_schema(item) for item in items], total

    async def create_table(self, payload: TableCreate) -> Table:
        table = MetadataTable(
            id=uuid.uuid4(),
            source_id=payload.source_id,
            name=payload.name,
            type=payload.type,
            description=payload.description,
            tags=payload.tags,
            schema_name=payload.schema_name,
            qualified_name=payload.qualified_name,
        )
        await self.repo.add(table)
        await self.session.commit()
        return self._to_schema(table)

    async def get_table(self, table_id: str) -> Table:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        return self._to_schema(table)

    async def update_table(self, table_id: str, payload: TableUpdate) -> Table:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(table, key, value)
        await self.session.commit()
        await self.session.refresh(table)
        return self._to_schema(table)

    async def delete_table(self, table_id: str) -> None:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        await self.repo.delete(table)
        await self.session.commit()

    @staticmethod
    def _to_schema(table: MetadataTable) -> Table:
        return Table.model_validate(table, from_attributes=True)
