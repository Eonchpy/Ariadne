from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.field import Field, FieldCreate, FieldUpdate
from app.services.field_service import FieldService
from app.db import get_db_session

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=Field, status_code=status.HTTP_201_CREATED)
async def create_field(payload: FieldCreate, session: AsyncSession = Depends(get_db_session)):
    service = FieldService(session)
    return await service.create_field(payload)


@router.get("/{field_id}", response_model=Field)
async def get_field(field_id: str, session: AsyncSession = Depends(get_db_session)):
    service = FieldService(session)
    return await service.get_field(field_id)


@router.put("/{field_id}", response_model=Field)
async def update_field(field_id: str, payload: FieldUpdate, session: AsyncSession = Depends(get_db_session)):
    service = FieldService(session)
    return await service.update_field(field_id, payload)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(field_id: str, session: AsyncSession = Depends(get_db_session)):
    service = FieldService(session)
    await service.delete_field(field_id)
    return None
