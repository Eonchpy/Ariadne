from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api import deps
from app.schemas.user import User
from app.schemas.lineage import (
    FieldTraceResponse,
    LineageGraphResponse,
    TableLineageCreateRequest,
    FieldLineageCreateRequest,
    LineageRelationship,
)
from app.services.lineage_service import LineageService
from app.graph.client import neo4j_dependency
from app.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/lineage", tags=["lineage"])


@router.post("/table", response_model=LineageRelationship, status_code=status.HTTP_201_CREATED)
async def create_table_lineage(
    payload: TableLineageCreateRequest,
    driver=Depends(neo4j_dependency),
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
):
    service = LineageService(driver)
    return await service.create_table_lineage(
        source_table_id=payload.source_table_id,
        target_table_id=payload.target_table_id,
        lineage_source=payload.lineage_source,
        transformation_type=payload.transformation_type,
        transformation_logic=payload.transformation_logic,
        confidence=payload.confidence,
    )


@router.post("/field", response_model=LineageRelationship, status_code=status.HTTP_201_CREATED)
async def create_field_lineage(
    payload: FieldLineageCreateRequest,
    driver=Depends(neo4j_dependency),
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
):
    service = LineageService(driver)
    return await service.create_field_lineage(
        source_field_id=payload.source_field_id,
        target_field_id=payload.target_field_id,
        lineage_source=payload.lineage_source,
        transformation_logic=payload.transformation_logic,
        confidence=payload.confidence,
    )


@router.get("/table/{table_id}/upstream", response_model=LineageGraphResponse)
async def get_upstream(
    table_id: str,
    depth: int = 3,
    granularity: str = "table",
    driver=Depends(neo4j_dependency),
    session: AsyncSession = Depends(get_db_session),
):
    service = LineageService(driver, db_session=session)
    return await service.get_upstream(table_id, depth, granularity)


@router.get("/table/{table_id}/downstream", response_model=LineageGraphResponse)
async def get_downstream(
    table_id: str,
    depth: int = 3,
    granularity: str = "table",
    driver=Depends(neo4j_dependency),
    session: AsyncSession = Depends(get_db_session),
):
    service = LineageService(driver, db_session=session)
    return await service.get_downstream(table_id, depth, granularity)


@router.get("/graph", response_model=LineageGraphResponse)
async def get_graph(
    table_id: str,
    direction: str = "downstream",
    depth: int = 3,
    driver=Depends(neo4j_dependency),
    session: AsyncSession = Depends(get_db_session),
):
    service = LineageService(driver, db_session=session)
    return await service.get_graph(table_id=table_id, depth=depth, direction=direction)


@router.delete("/{rel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lineage(
    rel_id: int,
    driver=Depends(neo4j_dependency),
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
):
    service = LineageService(driver)
    await service.delete_lineage(rel_id)


@router.get("/trace/field/{field_id}", response_model=FieldTraceResponse)
async def trace_field(
    field_id: str,
    direction: str = "both",
    depth: int = 5,
    driver=Depends(neo4j_dependency),
    session: AsyncSession = Depends(get_db_session),
):
    service = LineageService(driver, db_session=session)
    return await service.trace_field(field_id=field_id, direction=direction, depth=depth)
