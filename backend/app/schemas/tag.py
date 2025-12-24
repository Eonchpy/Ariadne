import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    name: str
    parent_id: Optional[uuid.UUID] = None
    level: int = Field(ge=1, le=3)

    model_config = ConfigDict(populate_by_name=True)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None


class Tag(TagBase):
    id: uuid.UUID
    path: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class TagWithChildren(Tag):
    children: List["TagWithChildren"] = Field(default_factory=list)


class TagTreeResponse(BaseModel):
    items: List[TagWithChildren]


class TagListResponse(BaseModel):
    items: List[Tag]


class TagUsageResponse(BaseModel):
    tag_id: uuid.UUID
    tag_name: str
    table_count: int
    tables: List[dict]


class TableTagsAddRequest(BaseModel):
    tag_ids: List[uuid.UUID]

