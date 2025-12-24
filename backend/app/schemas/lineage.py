from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class LineageSource(str, Enum):
    manual = "manual"
    approved = "approved"
    inferred = "inferred"


class TableLineageCreateRequest(BaseModel):
    source_table_id: str
    target_table_id: str
    lineage_source: LineageSource = LineageSource.manual
    transformation_type: Optional[str] = None
    transformation_logic: Optional[str] = None
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1 for inferred lineage",
    )


class FieldLineageCreateRequest(BaseModel):
    source_field_id: str
    target_field_id: str
    lineage_source: LineageSource = LineageSource.manual
    transformation_logic: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class LineageRelationship(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    lineage_source: LineageSource
    transformation_type: Optional[str] = None
    transformation_logic: Optional[str] = None
    confidence: Optional[float] = None


class LineageGraphNode(BaseModel):
    id: str
    label: Optional[str] = None
    type: str = "table"
    source_id: Optional[str] = None
    parent_id: Optional[str] = None
    ordinal_position: Optional[int] = None


class LineageGraphEdge(BaseModel):
    id: str
    from_: str = Field(alias="from")
    to: str
    type: Optional[str] = Field(default=None, alias="type")
    lineage_source: Optional[LineageSource] = None
    confidence: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class LineageGraphResponse(BaseModel):
    root_id: str
    nodes: list[LineageGraphNode] = Field(default_factory=list)
    edges: list[LineageGraphEdge] = Field(default_factory=list)

    @field_validator("nodes", "edges", mode="before")
    @classmethod
    def default_empty(cls, v):
        return v or []
