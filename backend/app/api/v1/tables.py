from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.table import Table, TableCreate, TableDetail, TableList, TableUpdate
from app.services.table_service import TableService
from app.services.field_service import FieldService
from app.schemas.field import FieldList
from app.db import get_db_session

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=TableList)
async def list_tables(
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    size: int = 20,
):
    table_service = TableService(session)
    items, total = await table_service.list_tables(page=page, size=size)
    pages = (total + size - 1) // size if size else 0
    return TableList(total=total, page=page, size=size, pages=pages, items=items)


@router.post("", response_model=Table, status_code=status.HTTP_201_CREATED)
async def create_table(payload: TableCreate, session: AsyncSession = Depends(get_db_session)):
    table_service = TableService(session)
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
):
    table_service = TableService(session)
    return await table_service.update_table(table_id, payload)


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(table_id: str, session: AsyncSession = Depends(get_db_session)):
    table_service = TableService(session)
    await table_service.delete_table(table_id)
    return None


@router.get("/{table_id}/fields", response_model=FieldList, tags=["fields"])
async def list_table_fields(table_id: str, session: AsyncSession = Depends(get_db_session)):
    field_service = FieldService(session)
    fields = await field_service.list_fields_for_table(table_id)
    return FieldList(items=fields)
