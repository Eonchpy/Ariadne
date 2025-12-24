import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.field import Field as FieldSchema


class TableBase(BaseModel):
    source_id: str | None = None
    name: str
    type: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    schema_name: str | None = None
    qualified_name: str | None = None


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    schema_name: str | None = None
    qualified_name: str | None = None


class Table(BaseModel):
    id: str | uuid.UUID
    source_id: str | uuid.UUID
    name: str
    type: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    row_count: int | None = None
    field_count: int | None = None
    schema_name: str | None = None
    qualified_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class TableDetail(Table):
    fields: list[FieldSchema] = Field(default_factory=list)


class TableList(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    items: list[Table]
