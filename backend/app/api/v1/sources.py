from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.source import Source, SourceCreate, SourceList, SourceUpdate, ConnectionTestResult
from app.services.source_service import SourceService
from app.db import get_db_session
from app.services.introspection_service import IntrospectionService
from app.schemas.table import TableDetail
from pydantic import BaseModel
from app.services.connection_service import ConnectionService
from app.repositories.audit_repo import ConnectionTestLogRepository
from app.models.audit import ConnectionTestLog
from app.api import deps
from app.services.tag_service import TagService

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
    tag_service = TagService(session)
    return await service.create_source(payload, tag_service=tag_service)


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


@router.post("/{source_id}/test", response_model=ConnectionTestResult)
async def test_source_connection(
    source_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = SourceService(session)
    return await service.test_connection(source_id)


@router.post("/test-connection", response_model=ConnectionTestResult, tags=["sources"])
async def test_connection_precreate(
    payload: SourceCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(deps.get_current_user),
):
    audit_repo = ConnectionTestLogRepository(session)
    tested_by = current_user.email if current_user else None
    service = ConnectionService(
        source_type=payload.type,
        connection_config=payload.connection_config or {},
        audit_repo=audit_repo,
    )
    return await service.test_connection(source_id=None, tested_by=tested_by)


class IntrospectionRequest(BaseModel):
    table_name: str
    schema_name: str | None = None


@router.post("/{source_id}/introspect/table", response_model=TableDetail)
async def introspect_table(
    source_id: str,
    body: IntrospectionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(deps.get_current_user),
):
    source_service = SourceService(session)
    source = await source_service._get_entity(source_id)
    service = IntrospectionService(source.type, source.connection_config or {})
    try:
        result = await service.introspect_table(body.table_name, body.schema_name)
        audit_repo = ConnectionTestLogRepository(session)
        await audit_repo.add(
            ConnectionTestLog(
                source_id=source.id,
                operation="introspection",
                table_name=body.table_name,
                tested_by=current_user.email if current_user else None,
                result="success",
                error_message=None,
            )
        )
        await session.commit()
        return result
    except Exception as exc:
        audit_repo = ConnectionTestLogRepository(session)
        await audit_repo.add(
            ConnectionTestLog(
                source_id=source.id,
                operation="introspection",
                table_name=body.table_name,
                tested_by=current_user.email if current_user else None,
                result="failure",
                error_message=str(exc),
            )
        )
        await session.commit()
        raise
