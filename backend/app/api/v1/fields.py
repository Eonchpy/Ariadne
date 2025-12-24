from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.field import Field, FieldCreate, FieldUpdate, FieldList
from app.services.field_service import FieldService
from app.db import get_db_session
from app.graph.client import neo4j_dependency

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=Field, status_code=status.HTTP_201_CREATED)
async def create_field(payload: FieldCreate, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    service = FieldService(session, lineage_driver=neo4j_driver)
    return await service.create_field(payload)


@router.get("/{field_id}", response_model=Field)
async def get_field(field_id: str, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    service = FieldService(session, lineage_driver=neo4j_driver)
    return await service.get_field(field_id)


@router.put("/{field_id}", response_model=Field)
async def update_field(field_id: str, payload: FieldUpdate, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    service = FieldService(session, lineage_driver=neo4j_driver)
    return await service.update_field(field_id, payload)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(field_id: str, session: AsyncSession = Depends(get_db_session), neo4j_driver=Depends(neo4j_dependency)):
    service = FieldService(session, lineage_driver=neo4j_driver)
    await service.delete_field(field_id)
    return None


@router.post("/batch", response_model=FieldList, status_code=status.HTTP_201_CREATED)
async def create_fields_batch(
    payload: list[FieldCreate],
    session: AsyncSession = Depends(get_db_session),
    neo4j_driver=Depends(neo4j_dependency),
):
    service = FieldService(session, lineage_driver=neo4j_driver)
    created = await service.create_fields_batch(table_id=payload[0].table_id if payload else "", payloads=payload)
    return FieldList(items=created)
