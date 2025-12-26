import uuid
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.table import MetadataTable
from app.repositories.table_repo import TableRepository
from app.schemas.table import Table, TableCreate, TableUpdate, TagSummary
from app.services.lineage_service import LineageService
from app.repositories.tag_repo import TagRepository
from app.repositories.source_repo import SourceRepository
from app.models.tag import Tag


class TableService:
    """PostgreSQL-backed table service."""

    def __init__(self, session: AsyncSession, lineage_driver=None):
        self.session = session
        self.repo = TableRepository(session)
        self.lineage_driver = lineage_driver
        self.tag_repo = TagRepository(session)
        self.source_repo = SourceRepository(session)

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
        return [await self._to_schema_with_tags(item) for item in items], total

    async def create_table(self, payload: TableCreate) -> Table:
        tag_ids = payload.tag_ids or []
        primary_tag_id = payload.primary_tag_id

        if not primary_tag_id:
            ds_tag = await self._get_datasource_tag_for_source(payload.source_id) if payload.source_id else None
            if ds_tag:
                primary_tag_id = str(ds_tag.id)
                if primary_tag_id not in tag_ids:
                    tag_ids.append(primary_tag_id)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="primary_tag_id required")

        if primary_tag_id and primary_tag_id not in tag_ids:
            tag_ids.append(primary_tag_id)

        # ensure UUID instances for persistence
        primary_tag_uuid = uuid.UUID(primary_tag_id) if primary_tag_id else None
        tag_uuid_list = [uuid.UUID(t) for t in tag_ids] if tag_ids else []

        table = MetadataTable(
            id=uuid.uuid4(),
            source_id=payload.source_id,
            name=payload.name,
            name_normalized=payload.name.lower() if payload.name else None,
            type=payload.type,
            description=payload.description,
            tags=payload.tags,
            schema_name=payload.schema_name,
            qualified_name=payload.qualified_name,
            primary_tag_id=primary_tag_uuid,
        )
        try:
            await self.repo.add(table)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Table name already exists under this data source",
            ) from exc

        if tag_uuid_list:
            await self.tag_repo.add_table_tags(table.id, tag_uuid_list)
            await self.session.commit()

        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_table_node(
                {
                    "id": str(table.id),
                    "name": table.name,
                    "schema_name": table.schema_name,
                    "qualified_name": table.qualified_name,
                    "source_id": str(table.source_id) if table.source_id else None,
                }
            )
        return await self._to_schema_with_tags(table)

    async def get_table(self, table_id: str) -> Table:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        return await self._to_schema_with_tags(table)

    async def update_table(self, table_id: str, payload: TableUpdate) -> Table:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        updates = payload.model_dump(exclude_unset=True)
        tag_ids = updates.pop("tag_ids", None)
        primary_tag_id = updates.pop("primary_tag_id", None)

        for key, value in updates.items():
            setattr(table, key, value)
            if key == "name" and value:
                table.name_normalized = value.lower()

        if tag_ids is not None:
            await self.tag_repo.remove_all_tags_for_table(table.id)
            tag_uuid_list = [uuid.UUID(t) for t in tag_ids]
            await self.tag_repo.add_table_tags(table.id, tag_uuid_list)
            await self.session.commit()

        if primary_tag_id:
            current_tags = [str(t.id) for t in await self.tag_repo.list_table_tags(table.id)]
            if primary_tag_id not in current_tags:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="primary_tag_id must be in table tags")
            table.primary_tag_id = uuid.UUID(primary_tag_id)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Table name already exists under this data source",
            ) from exc
        await self.session.refresh(table)
        if self.lineage_driver:
            await LineageService(self.lineage_driver).sync_table_node(
                {
                    "id": str(table.id),
                    "name": table.name,
                    "schema_name": table.schema_name,
                    "qualified_name": table.qualified_name,
                    "source_id": str(table.source_id) if table.source_id else None,
                }
            )
        return await self._to_schema_with_tags(table)

    async def delete_table(self, table_id: str) -> None:
        table = await self.repo.get(table_id)
        if not table:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        await self.repo.delete(table)
        await self.session.commit()
        if self.lineage_driver:
            await LineageService(self.lineage_driver).delete_table_node(str(table.id))

    async def _to_schema_with_tags(self, table: MetadataTable) -> Table:
        tags = await self.tag_repo.list_table_tags(table.id)
        tag_summaries = [
            TagSummary(id=str(t.id), name=t.name, path=getattr(t, "path", None), level=getattr(t, "level", None))
            for t in tags
        ]
        primary = next((t for t in tag_summaries if t.id == str(table.primary_tag_id)), None)
        return Table(
            id=str(table.id),
            source_id=str(table.source_id) if table.source_id else None,
            name=table.name,
            type=table.type,
            description=table.description,
            tags=table.tags,
            tag_ids=[str(t.id) for t in tags],
            primary_tag_id=str(table.primary_tag_id) if table.primary_tag_id else None,
            primary_tag=primary,
            row_count=table.row_count,
            field_count=table.field_count,
            schema_name=table.schema_name,
            qualified_name=table.qualified_name,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )

    async def _get_datasource_tag_for_source(self, source_id: str):
        source = await self.source_repo.get(source_id)
        if not source:
            return None
        path = f"DataSource-{source.type}-{source.name}"
        result = await self.session.execute(select(Tag).where(Tag.path == path))
        return result.scalars().first()
