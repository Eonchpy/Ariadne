import uuid
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.table import MetadataTable
from app.repositories.table_repo import TableRepository
from app.schemas.table import Table, TableCreate, TableUpdate
from app.services.lineage_service import LineageService


class TableService:
    """PostgreSQL-backed table service."""

    def __init__(self, session: AsyncSession, lineage_driver=None):
        self.session = session
        self.repo = TableRepository(session)
        self.lineage_driver = lineage_driver

    async def list_tables(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        source_id: str | None = None,
        tag_ids: list[str] | None = None,
        tag_match: str | None = "any",
        include_subtags: bool = False,
    ) -> Tuple[list[Table], int]:
        items, total = await self.repo.paginate(
            page=page,
            size=size,
            search=search,
            source_id=source_id,
            tag_ids=tag_ids,
            tag_match=tag_match,
            include_subtags=include_subtags,
        )
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
        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_table_node(table.to_dict() if hasattr(table, "to_dict") else {
                "id": str(table.id),
                "name": table.name,
                "schema_name": table.schema_name,
                "qualified_name": table.qualified_name,
                "source_id": str(table.source_id) if table.source_id else None,
            })
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
        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_table_node(table.to_dict() if hasattr(table, "to_dict") else {
                "id": str(table.id),
                "name": table.name,
                "schema_name": table.schema_name,
                "qualified_name": table.qualified_name,
                "source_id": str(table.source_id) if table.source_id else None,
            })
        return self._to_schema(table)

    async def delete_table(self, table_id: str) -> None:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        await self.repo.delete(table)
        await self.session.commit()
        if self.lineage_driver:
            await LineageService(self.lineage_driver).delete_table_node(str(table.id))

    @staticmethod
    def _to_schema(table: MetadataTable) -> Table:
        return Table.model_validate(table, from_attributes=True)
