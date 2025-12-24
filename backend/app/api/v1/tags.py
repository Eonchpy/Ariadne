import uuid
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.tag import (
    TagTreeResponse,
    TagCreate,
    TagUpdate,
    Tag,
    TagUsageResponse,
    TagListResponse,
    TableTagsAddRequest,
)
from app.services.tag_service import TagService
from app.db import get_db_session

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(session: AsyncSession = Depends(get_db_session)) -> TagService:
    return TagService(session)


@router.get("", response_model=TagTreeResponse)
async def get_tags(
    level: Optional[int] = None,
    parent_id: Optional[uuid.UUID] = None,
    service: TagService = Depends(get_tag_service),
):
    items = await service.get_tag_tree(level=level, parent_id=parent_id)
    return TagTreeResponse(items=items)


@router.post("", response_model=Tag, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    current_user=Depends(deps.require_admin),
    service: TagService = Depends(get_tag_service),
):
    return await service.create_tag(payload, current_user)


@router.put("/{tag_id}", response_model=Tag)
async def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    current_user=Depends(deps.require_admin),
    service: TagService = Depends(get_tag_service),
):
    return await service.update_tag(tag_id, payload, current_user)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user=Depends(deps.require_admin),
    service: TagService = Depends(get_tag_service),
):
    await service.delete_tag(tag_id, current_user)
    return None


@router.get("/{tag_id}/usage", response_model=TagUsageResponse)
async def tag_usage(tag_id: uuid.UUID, service: TagService = Depends(get_tag_service)):
    return await service.get_tag_usage(tag_id)


@router.get("/tables/{table_id}", response_model=TagListResponse, tags=["table-tags"])
async def get_table_tags(table_id: uuid.UUID, service: TagService = Depends(get_tag_service)):
    items = await service.get_table_tags(table_id)
    return TagListResponse(items=items)


@router.post("/tables/{table_id}", status_code=status.HTTP_201_CREATED, tags=["table-tags"])
async def add_table_tags(
    table_id: uuid.UUID,
    payload: TableTagsAddRequest,
    service: TagService = Depends(get_tag_service),
):
    await service.add_tags_to_table(table_id, payload.tag_ids)
    return {"table_id": str(table_id), "added": [str(t) for t in payload.tag_ids]}


@router.delete("/tables/{table_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["table-tags"])
async def remove_table_tag(
    table_id: uuid.UUID,
    tag_id: uuid.UUID,
    service: TagService = Depends(get_tag_service),
):
    await service.remove_tag_from_table(table_id, tag_id)
    return None

