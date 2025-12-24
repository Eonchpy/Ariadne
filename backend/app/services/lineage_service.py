import uuid
from typing import Any

from fastapi import HTTPException, status
from neo4j import AsyncDriver

from app.schemas.lineage import (
    LineageGraphResponse,
    LineageGraphNode,
    LineageGraphEdge,
    LineageSource,
    LineageRelationship,
)
from app.graph import queries
import structlog


log = structlog.get_logger(__name__)


class LineageService:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def sync_table_node(self, table: dict[str, Any]) -> None:
        async with self.driver.session() as session:
            await session.run(
                queries.CREATE_TABLE_NODE,
                id=table["id"],
                name=table["name"],
                schema_name=table.get("schema_name"),
                qualified_name=table.get("qualified_name"),
                source_id=table.get("source_id"),
            )

    async def sync_field_node(self, field: dict[str, Any]) -> None:
        async with self.driver.session() as session:
            await session.run(
                queries.CREATE_FIELD_NODE,
                id=field["id"],
                name=field["name"],
                data_type=field.get("data_type"),
                table_id=field.get("table_id"),
            )

    async def delete_table_node(self, table_id: str) -> None:
        async with self.driver.session() as session:
            # delete field nodes of this table first to avoid orphans
            await session.run(queries.DELETE_FIELDS_BY_TABLE, table_id=table_id)
            await session.run(queries.DELETE_TABLE_NODE, id=table_id)

    async def delete_field_node(self, field_id: str) -> None:
        async with self.driver.session() as session:
            await session.run(queries.DELETE_FIELD_NODE, id=field_id)

    async def create_table_lineage(
        self,
        source_table_id: str,
        target_table_id: str,
        lineage_source: str | LineageSource,
        transformation_type: str | None,
        transformation_logic: str | None,
        confidence: float | None,
    ) -> LineageRelationship:
        async with self.driver.session() as session:
            result = await session.run(
                queries.CREATE_TABLE_LINEAGE,
                source_id=source_table_id,
                target_id=target_table_id,
                lineage_source=lineage_source.value if isinstance(lineage_source, LineageSource) else lineage_source,
                transformation_type=transformation_type,
                transformation_logic=transformation_logic,
                confidence=confidence,
            )
            record = await result.single()
            rel_id = record["rel_id"] if record else None

        return LineageRelationship(
            id=str(rel_id) if rel_id is not None else str(uuid.uuid4()),
            source_node_id=source_table_id,
            target_node_id=target_table_id,
            lineage_source=lineage_source,
            transformation_type=transformation_type,
            transformation_logic=transformation_logic,
            confidence=confidence,
        )

    async def create_field_lineage(
        self,
        source_field_id: str,
        target_field_id: str,
        lineage_source: str | LineageSource,
        transformation_logic: str | None,
        confidence: float | None,
    ) -> LineageRelationship:
        async with self.driver.session() as session:
            result = await session.run(
                queries.CREATE_FIELD_LINEAGE,
                source_id=source_field_id,
                target_id=target_field_id,
                lineage_source=lineage_source.value if isinstance(lineage_source, LineageSource) else lineage_source,
                transformation_logic=transformation_logic,
                confidence=confidence,
            )
            record = await result.single()
            rel_id = record["rel_id"] if record else None

        return LineageRelationship(
            id=str(rel_id) if rel_id is not None else str(uuid.uuid4()),
            source_node_id=source_field_id,
            target_node_id=target_field_id,
            lineage_source=lineage_source,
            transformation_logic=transformation_logic,
            confidence=confidence,
        )

    async def get_upstream(self, table_id: str, depth: int, granularity: str = "table") -> LineageGraphResponse:
        # granularity kept for backward compatibility; we now always return table+field lineage
        async with self.driver.session() as session:
            rel_filter = "<FEEDS_INTO"
            result = await session.run(queries.GET_UPSTREAM, table_id=table_id, depth=depth, rel_filter=rel_filter)
            record = await result.single()
            return self._to_graph(record)

    async def get_downstream(self, table_id: str, depth: int, granularity: str = "table") -> LineageGraphResponse:
        async with self.driver.session() as session:
            rel_filter = "FEEDS_INTO>"
            result = await session.run(queries.GET_DOWNSTREAM, table_id=table_id, depth=depth, rel_filter=rel_filter)
            record = await result.single()
            return self._to_graph(record)

    async def delete_lineage(self, rel_id: int) -> None:
        async with self.driver.session() as session:
            result = await session.run(queries.DELETE_LINEAGE, rel_id=rel_id)
            record = await result.single()
            deleted = record["deleted_count"] if record else 0
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Lineage relationship not found",
                )

    def _to_graph(self, record) -> LineageGraphResponse:
        if not record:
            return LineageGraphResponse(root_id="", nodes=[], edges=[])

        log.info("lineage_raw", rels=record.get("rels"), nodes=record.get("nodes"))
        nodes: list[LineageGraphNode] = []
        edges: list[LineageGraphEdge] = []

        for node in record.get("nodes") or []:
            # Neo4j returns Node objects; convert to a plain dict first.
            labels = []
            if isinstance(node, dict):
                props = node
            elif hasattr(node, "_properties"):
                props = getattr(node, "_properties", {}) or {}
                labels = list(getattr(node, "labels", []))
            else:  # best-effort fallback
                try:
                    props = dict(node)
                except Exception:
                    props = {}

            business_id = props.get("id")
            label = props.get("name")
            source_id = props.get("source_id")
            parent_id = props.get("table_id")  # table_id if it's a field
            ordinal_position = props.get("ordinal_position")

            node_type = "table"
            if "Field" in labels:
                node_type = "field"
            elif "Table" in labels:
                node_type = "table"

            if business_id:
                nodes.append(
                    LineageGraphNode(
                        id=business_id,
                        label=label,
                        type=node_type,
                        source_id=source_id,
                        parent_id=parent_id,
                        ordinal_position=ordinal_position,
                    )
                )

        for rel in record.get("rels") or []:
            data = rel if hasattr(rel, "items") else {}
            rel_id = data.get("id")
            start_id = data.get("from") or data.get("start") or data.get("start_id")
            end_id = data.get("to") or data.get("end") or data.get("end_id")
            lineage_source = data.get("lineage_source")
            confidence = data.get("confidence")
            rel_type = data.get("rel_type")
            edge_type = "field" if rel_type == "DERIVES_FROM" else "table"
            if not start_id or not end_id:
                continue
            edges.append(
                LineageGraphEdge(
                    id=str(rel_id) if rel_id is not None else "",
                    from_=start_id,
                    to=end_id,
                    type=edge_type,
                    lineage_source=lineage_source,
                    confidence=confidence,
                    metadata={"rel_type": rel_type} if rel_type else {},
                )
            )

        return LineageGraphResponse(
            root_id=record.get("root_id") or "",
            nodes=nodes,
            edges=edges,
        )
