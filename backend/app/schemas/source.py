import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    oracle = "oracle"
    mongodb = "mongodb"
    elasticsearch = "elasticsearch"
    other = "other"


class SourceBase(BaseModel):
    name: str
    type: SourceType
    description: str | None = None
    connection_config: dict[str, Any] | None = None


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    type: SourceType | None = None
    description: str | None = None
    connection_config: dict[str, Any] | None = None
    is_active: bool | None = None


class Source(SourceBase):
    id: str | uuid.UUID
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class SourceList(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    items: list[Source]
