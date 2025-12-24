from fastapi import APIRouter, Depends, status
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.table import Table, TableCreate, TableDetail, TableList, TableUpdate
from app.services.table_service import TableService
from app.services.field_service import FieldService
from app.services.tag_service import TagService
from app.schemas.field import FieldList, FieldCreate, FieldCreateInTable, Field
from app.db import get_db_session
from app.graph.client import neo4j_dependency

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=TableList)
async def list_tables(
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    source_id: str | None = None,
    tags: str | None = None,
    tag_match: str | None = "any",
    include_subtags: bool = False,
):
    table_service = TableService(session)
    tag_ids = tags.split(",") if tags else None
    items, total = await table_service.list_tables(
        page=page,
        size=size,
        search=search,
        source_id=source_id,
        tag_ids=tag_ids,
        tag_match=tag_match,
        include_subtags=include_subtags,
    )
    pages = (total + size - 1) // size if size else 0
    return TableList(total=total, page=page, size=size, pages=pages, items=items)


@router.post("", response_model=Table, status_code=status.HTTP_201_CREATED)
async def create_table(payload: TableCreate, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    table_service = TableService(session, lineage_driver=neo4j_driver)
    return await table_service.create_table(payload)


@router.get("/{table_id}", response_model=TableDetail)
async def get_table(table_id: str, session: AsyncSession = Depends(get_db_session)):
    table_service = TableService(session)
    field_service = FieldService(session)
    table = await table_service.get_table(table_id)
    fields = await field_service.list_fields_for_table(table_id)
    return TableDetail(**table.model_dump(), fields=fields)


@router.put("/{table_id}", response_model=Table)
async def update_table(
    table_id: str,
    payload: TableUpdate,
    session: AsyncSession = Depends(get_db_session),
    neo4j_driver=Depends(neo4j_dependency),
):
    table_service = TableService(session, lineage_driver=neo4j_driver)
    return await table_service.update_table(table_id, payload)


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(table_id: str, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    table_service = TableService(session, lineage_driver=neo4j_driver)
    await table_service.delete_table(table_id)
    return None


@router.get("/{table_id}/fields", response_model=FieldList, tags=["fields"])
async def list_table_fields(table_id: str, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    field_service = FieldService(session, lineage_driver=neo4j_driver)
    fields = await field_service.list_fields_for_table(table_id)
    return FieldList(items=fields)


@router.post("/{table_id}/fields", response_model=Field, tags=["fields"], status_code=status.HTTP_201_CREATED)
async def create_field_for_table(
    table_id: str,
    payload: FieldCreateInTable,
    session: AsyncSession = Depends(get_db_session),
    neo4j_driver=Depends(neo4j_dependency),
):
    field_service = FieldService(session, lineage_driver=neo4j_driver)
    created = await field_service.create_field(payload, table_id=table_id)
    return created


@router.post("/{table_id}/fields/batch", response_model=FieldList, tags=["fields"], status_code=status.HTTP_201_CREATED)
async def batch_create_fields(
    table_id: str,
    payload: list[FieldCreateInTable],
    session: AsyncSession = Depends(get_db_session),
    neo4j_driver=Depends(neo4j_dependency),
):
    field_service = FieldService(session, lineage_driver=neo4j_driver)
    created = await field_service.create_fields_batch(table_id=table_id, payloads=payload)
    return FieldList(items=created)


@router.get("/{table_id}/tags", tags=["table-tags"])
async def get_table_tags(
    table_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    tag_service = TagService(session)
    items = await tag_service.get_table_tags(uuid.UUID(table_id))
    return {"items": items}


@router.post("/{table_id}/tags", tags=["table-tags"], status_code=status.HTTP_201_CREATED)
async def add_table_tags(
    table_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_db_session),
):
    tag_ids = [uuid.UUID(t) for t in payload.get("tag_ids", [])]
    tag_service = TagService(session)
    await tag_service.add_tags_to_table(uuid.UUID(table_id), tag_ids)
    return {"table_id": table_id, "added": [str(t) for t in tag_ids]}


@router.delete("/{table_id}/tags/{tag_id}", tags=["table-tags"], status_code=status.HTTP_204_NO_CONTENT)
async def remove_table_tag(
    table_id: str,
    tag_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    tag_service = TagService(session)
    await tag_service.remove_tag_from_table(uuid.UUID(table_id), uuid.UUID(tag_id))
    return None
