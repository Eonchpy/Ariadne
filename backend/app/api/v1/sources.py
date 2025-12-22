from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.source import Source, SourceCreate, SourceList, SourceUpdate
from app.services.source_service import SourceService
from app.db import get_db_session

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=SourceList)
async def list_sources(
    session: AsyncSession = Depends(get_db_session),
    page: int = 1,
    size: int = 20,
):
    service = SourceService(session)
    items, total = await service.list_sources(page=page, size=size)
    pages = (total + size - 1) // size if size else 0
    return SourceList(total=total, page=page, size=size, pages=pages, items=items)


@router.post("", response_model=Source, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    session: AsyncSession = Depends(get_db_session),
):
    service = SourceService(session)
    return await service.create_source(payload)


@router.get("/{source_id}", response_model=Source)
async def get_source(
    source_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = SourceService(session)
    return await service.get_source(source_id)


@router.put("/{source_id}", response_model=Source)
async def update_source(
    source_id: str,
    payload: SourceUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    service = SourceService(session)
    return await service.update_source(source_id, payload)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = SourceService(session)
    await service.delete_source(source_id)
    return None
