import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag as TagModel, TableTag
from app.repositories.tag_repo import TagRepository
from app.schemas.tag import (
    Tag,
    TagCreate,
    TagUpdate,
    TagWithChildren,
    TagUsageResponse,
)
from app.schemas.user import User


class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TagRepository(session)

    async def _is_admin(self, user: User):
        if not user or "admin" not in (user.roles or []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    async def get_tag_tree(self, level: Optional[int] = None, parent_id: Optional[uuid.UUID] = None) -> List[TagWithChildren]:
        tags = await self.repo.list_by_filters(level=level, parent_id=parent_id)
        tag_map = {
            t.id: TagWithChildren(
                id=t.id,
                name=t.name,
                parent_id=t.parent_id,
                level=t.level,
                path=t.path,
                created_at=t.created_at,
                updated_at=t.updated_at,
                children=[],
            )
            for t in tags
        }
        roots: List[TagWithChildren] = []
        for tag in tag_map.values():
            if tag.parent_id and tag.parent_id in tag_map:
                tag_map[tag.parent_id].children.append(tag)
            else:
                roots.append(tag)
        return roots

    async def create_tag(self, payload: TagCreate, user: User) -> Tag:
        await self._is_admin(user)
        parent = None
        if payload.parent_id:
            parent = await self.repo.get(payload.parent_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent tag not found")
        path = payload.name if not parent else f"{parent.path}-{payload.name}"
        # explicit uniqueness check to return clear message before DB constraint
        existing = await self.session.execute(select(TagModel).where(TagModel.path == path))
        if existing.scalars().first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag path already exists")
        tag = TagModel(
            id=uuid.uuid4(),
            name=payload.name,
            parent_id=payload.parent_id,
            level=payload.level,
            path=path,
        )
        self.session.add(tag)
        try:
            await self.session.commit()
        except Exception as exc:  # unique path, etc.
            await self.session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag conflict") from exc
        return Tag.model_validate(tag, from_attributes=True)

    async def update_tag(self, tag_id: uuid.UUID, payload: TagUpdate, user: User) -> Tag:
        await self._is_admin(user)
        tag = await self.repo.get(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        if payload.name:
            tag.name = payload.name
            # recompute path for tag and descendants
            await self._recompute_paths(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return Tag.model_validate(tag, from_attributes=True)

    async def _recompute_paths(self, tag: TagModel):
        # recompute self path
        parent = None
        if tag.parent_id:
            parent = await self.repo.get(tag.parent_id)
        tag.path = tag.name if not parent else f"{parent.path}-{tag.name}"
        await self.session.flush()
        # update descendants
        descendants = await self.session.execute(
            select(TagModel).where(TagModel.parent_id == tag.id)
        )
        for child in descendants.scalars().all():
            await self._recompute_paths(child)

    async def delete_tag(self, tag_id: uuid.UUID, user: User) -> None:
        await self._is_admin(user)
        tag = await self.repo.get(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        # has children?
        children = await self.repo.list_by_filters(parent_id=tag_id)
        if children:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag has children")
        # in use?
        total, _ = await self.repo.tag_usage(tag_id)
        if total:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag in use")
        await self.session.delete(tag)
        await self.session.commit()

    async def get_tag_usage(self, tag_id: uuid.UUID) -> TagUsageResponse:
        tag = await self.repo.get(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        total, table_ids = await self.repo.tag_usage(tag_id)
        tables = [{"id": str(tid)} for tid in table_ids]
        return TagUsageResponse(tag_id=tag.id, tag_name=tag.name, table_count=total, tables=tables)

    async def add_tags_to_table(self, table_id: uuid.UUID, tag_ids: List[uuid.UUID]) -> None:
        await self.repo.add_table_tags(table_id, tag_ids)
        await self.session.commit()

    async def remove_tag_from_table(self, table_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        await self.repo.remove_table_tag(table_id, tag_id)
        await self.session.commit()

    async def get_table_tags(self, table_id: uuid.UUID) -> List[Tag]:
        tags = await self.repo.list_table_tags(table_id)
        return [Tag.model_validate(t, from_attributes=True) for t in tags]

    async def get_or_create_tag(self, name: str, level: int, parent_id: uuid.UUID | None) -> Tag:
        existing = await self.session.execute(
            select(TagModel).where(and_(TagModel.name == name, TagModel.level == level, TagModel.parent_id == parent_id))
        )
        tag = existing.scalars().first()
        if tag:
            return Tag.model_validate(tag, from_attributes=True)
        create_payload = TagCreate(name=name, level=level, parent_id=parent_id)
        system_user = User(
            id=str(uuid.uuid4()),
            email="system@example.com",
            name="system",
            roles=["admin"],
        )
        return await self.create_tag(create_payload, user=system_user)
