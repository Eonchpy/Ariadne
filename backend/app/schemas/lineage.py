from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Literal

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
    primary_tag: Optional[dict[str, Any]] = None
    distance: Optional[int] = None
    source_name: Optional[str] = None


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


class TracePathItem(BaseModel):
    table_id: str
    table_name: Optional[str] = None
    field_id: str
    field_name: Optional[str] = None
    distance: int
    primary_tag_path: Optional[str] = None
    source_name: Optional[str] = None


class TracePath(BaseModel):
    upstream: list[TracePathItem] = Field(default_factory=list)
    downstream: list[TracePathItem] = Field(default_factory=list)


class FieldRef(BaseModel):
    id: str
    name: Optional[str] = None
    table_id: str
    table_name: Optional[str] = None


class FieldTraceResponse(BaseModel):
    field: FieldRef
    trace_path: TracePath
    involved_tables: list[str] = Field(default_factory=list)
    involved_fields: list[str] = Field(default_factory=list)


class PathItem(BaseModel):
    path: list[str] = Field(default_factory=list)
    length: int | None = None


class PathsResponse(BaseModel):
    nodes: list[LineageGraphNode] = Field(default_factory=list)
    edges: list[LineageGraphEdge] = Field(default_factory=list)
    paths: list[PathItem] = Field(default_factory=list)


class CycleListResponse(BaseModel):
    cycles: list[list[str]] = Field(default_factory=list)
    nodes: list[LineageGraphNode] = Field(default_factory=list)
    edges: list[LineageGraphEdge] = Field(default_factory=list)


class ImpactNodeSummary(BaseModel):
    id: str
    distance: int | None = None
    type: str | None = None
    primary_tag: Optional[dict[str, Any]] = None
    source_name: Optional[str] = None


class ImpactAnalysisResponse(BaseModel):
    root_id: str
    direction: str
    depth: int
    nodes: list[LineageGraphNode] = Field(default_factory=list)
    edges: list[LineageGraphEdge] = Field(default_factory=list)
    impacted: list[ImpactNodeSummary] = Field(default_factory=list)


class DomainGroup(BaseModel):
    tag_id: Optional[str] = None
    tag_name: Optional[str] = None
    tag_path: Optional[str] = None
    table_count: int
    severity: Literal["high", "medium", "low"]
    sample_tables: list[dict[str, Any]] = Field(default_factory=list)


class BlastRadiusResponse(BaseModel):
    root_id: str
    direction: Literal["upstream", "downstream"]
    depth: int
    granularity: Literal["table", "field"] = "table"
    total_impacted_tables: int
    total_impacted_fields: int
    total_impacted_domains: int
    max_depth_reached: int
    severity_level: Literal["high", "medium", "low"]
    domain_groups: list[DomainGroup] = Field(default_factory=list)
    depth_map: dict[int, int] = Field(default_factory=dict)


class QualityCheckNode(BaseModel):
    id: str
    name: Optional[str] = None
    primary_tag_path: Optional[str] = None
    source_name: Optional[str] = None
    type: Literal["table", "field"] = "table"


class QualityCheckResponse(BaseModel):
    has_cycles: bool
    cycles: list[list[QualityCheckNode]] = Field(default_factory=list)
    severity_level: Literal["high", "low"]
    issue_count: int
    audit_timestamp: str


class LineageRelationshipNode(BaseModel):
    id: str
    name: Optional[str] = None
    type: Literal["table", "field"] | str = "table"


class LineageRelationshipTransformation(BaseModel):
    type: Optional[str] = None
    logic: Optional[str] = None
    description: Optional[str] = None


class LineageRelationshipMetadata(BaseModel):
    source: Optional[str] = None
    confidence: Optional[float] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None


class LineageRelationshipDetail(BaseModel):
    id: str
    source: LineageRelationshipNode
    target: LineageRelationshipNode
    transformation: LineageRelationshipTransformation
    metadata: LineageRelationshipMetadata
