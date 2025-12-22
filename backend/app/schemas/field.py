import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FieldBase(BaseModel):
    table_id: str
    name: str
    data_type: str
    description: str | None = None
    is_nullable: bool | None = None
    is_primary_key: bool | None = None
    is_foreign_key: bool | None = None


class FieldCreate(FieldBase):
    pass


class FieldUpdate(BaseModel):
    name: str | None = None
    data_type: str | None = None
    description: str | None = None
    is_nullable: bool | None = None
    is_primary_key: bool | None = None
    is_foreign_key: bool | None = None


class Field(BaseModel):
    id: str | uuid.UUID
    table_id: str | uuid.UUID
    name: str
    data_type: str
    description: str | None = None
    is_nullable: bool | None = None
    is_primary_key: bool | None = None
    is_foreign_key: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class FieldList(BaseModel):
    items: list[Field]
