import uuid
from collections import deque
from typing import Any

from fastapi import HTTPException, status
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.lineage import (
    FieldTraceResponse,
    FieldRef,
    TracePath,
    TracePathItem,
    LineageGraphResponse,
    LineageGraphNode,
    LineageGraphEdge,
    LineageSource,
    LineageRelationship,
)
from app.graph import queries
from app.repositories.table_repo import TableRepository
from app.repositories.field_repo import FieldRepository
import structlog


log = structlog.get_logger(__name__)


class LineageService:
    def __init__(self, driver: AsyncDriver, db_session: AsyncSession | None = None):
        self.driver = driver
        self.db_session = db_session

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

    async def get_graph(self, table_id: str, depth: int = 3, direction: str = "downstream") -> LineageGraphResponse:
        rel_filter = "FEEDS_INTO>"
        if direction == "upstream":
            rel_filter = "<FEEDS_INTO"
        elif direction == "both":
            rel_filter = "FEEDS_INTO>|<FEEDS_INTO"

        async with self.driver.session() as session:
            result = await session.run(queries.GET_GRAPH, table_id=table_id, depth=depth, rel_filter=rel_filter)
            record = await result.single()
            if record is None:
                # Fallback: return the focal table node if it exists in PG even when Neo4j has no entry yet.
                return await self._root_only_graph(table_id)
            return await self._to_graph(record)

    async def get_upstream(self, table_id: str, depth: int, granularity: str = "table") -> LineageGraphResponse:
        return await self.get_graph(table_id, depth=depth, direction="upstream")

    async def get_downstream(self, table_id: str, depth: int, granularity: str = "table") -> LineageGraphResponse:
        return await self.get_graph(table_id, depth=depth, direction="downstream")

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

    async def trace_field(self, field_id: str, direction: str = "both", depth: int = 5) -> FieldTraceResponse:
        if not self.db_session:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB session required")

        field_repo = FieldRepository(self.db_session)
        table_repo = TableRepository(self.db_session)

        base_field = await field_repo.get(field_id)
        if not base_field:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

        async with self.driver.session() as session:
            upstream_records = []
            downstream_records = []
            if direction in ("upstream", "both"):
                upstream_cursor = await session.run(
                    queries.TRACE_FIELD_UPSTREAM, field_id=field_id, depth=depth
                )
                upstream_records = [dict(record) async for record in upstream_cursor]
            if direction in ("downstream", "both"):
                downstream_cursor = await session.run(
                    queries.TRACE_FIELD_DOWNSTREAM, field_id=field_id, depth=depth
                )
                downstream_records = [dict(record) async for record in downstream_cursor]

        table_ids = {base_field.table_id}
        for rec in upstream_records + downstream_records:
            if rec.get("table_id"):
                table_ids.add(uuid.UUID(str(rec["table_id"])))

        table_map = await table_repo.get_tables_with_primary_tags(list(table_ids))

        def to_item(rec: dict) -> TracePathItem:
            tbl = table_map.get(str(rec.get("table_id"))) or {}
            return TracePathItem(
                table_id=str(rec.get("table_id")),
                table_name=tbl.get("name"),
                field_id=str(rec.get("field_id")),
                field_name=rec.get("field_name"),
                distance=int(rec.get("distance", 0)),
                primary_tag_path=(tbl.get("primary_tag") or {}).get("path"),
                source_name=tbl.get("source_name"),
            )

        upstream_items = [to_item(r) for r in upstream_records]
        downstream_items = [to_item(r) for r in downstream_records]

        base_table = table_map.get(str(base_field.table_id)) or {}
        field_ref = FieldRef(
            id=str(base_field.id),
            name=getattr(base_field, "name", None),
            table_id=str(base_field.table_id),
            table_name=base_table.get("name"),
        )

        involved_tables = list({str(t.table_id) for t in [base_field]})
        involved_tables.extend([item.table_id for item in upstream_items + downstream_items])
        involved_tables = [t for t in dict.fromkeys(involved_tables) if t]
        involved_fields = [field_ref.id] + [item.field_id for item in upstream_items + downstream_items]
        involved_fields = [f for f in dict.fromkeys(involved_fields) if f]

        return FieldTraceResponse(
            field=field_ref,
            trace_path=TracePath(upstream=upstream_items, downstream=downstream_items),
            involved_tables=involved_tables,
            involved_fields=involved_fields,
        )

    async def _to_graph(self, record) -> LineageGraphResponse:
        # always return root node even if no edges
        if not record:
            return LineageGraphResponse(root_id="", nodes=[], edges=[])

        log.info("lineage_raw", rels=record.get("rels"), nodes=record.get("nodes"))
        nodes: list[LineageGraphNode] = []
        edges: list[LineageGraphEdge] = []

        for node in record.get("nodes") or []:
            labels = []
            if isinstance(node, dict):
                props = node
            elif hasattr(node, "_properties"):
                props = getattr(node, "_properties", {}) or {}
                labels = list(getattr(node, "labels", []))
            else:
                try:
                    props = dict(node)
                except Exception:
                    props = {}

            business_id = props.get("id")
            label = props.get("name")
            source_id = props.get("source_id")
            parent_id = props.get("table_id")  # table_id if it's a field
            ordinal_position = props.get("ordinal_position")
            distance = props.get("depth") or props.get("distance")

            node_type = "table"
            if "Field" in labels:
                node_type = "field"
            elif "Table" in labels:
                node_type = "table"
            elif props.get("table_id"):
                # heuristically treat nodes with table_id property as field nodes when labels missing
                node_type = "field"

            if business_id:
                nodes.append(
                    LineageGraphNode(
                        id=business_id,
                        label=label,
                        type=node_type,
                        source_id=source_id,
                        parent_id=parent_id,
                        ordinal_position=ordinal_position,
                        distance=distance if distance is not None else (0 if business_id == record.get("root_id") else None),
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

        # ensure root node exists
        root_id = record.get("root_id")
        if root_id and not any(n.id == root_id for n in nodes):
            nodes.append(LineageGraphNode(id=root_id, label=None, type="table", distance=0))

        # compute distance using BFS if missing
        if root_id:
            adjacency: dict[str, set[str]] = {}
            for e in edges:
                adjacency.setdefault(e.from_, set()).add(e.to)
                adjacency.setdefault(e.to, set()).add(e.from_)
            dist: dict[str, int] = {str(root_id): 0}
            q: deque[str] = deque([str(root_id)])
            while q:
                cur = q.popleft()
                for nxt in adjacency.get(cur, []):
                    if nxt not in dist:
                        dist[nxt] = dist[cur] + 1
                        q.append(nxt)
            enriched = []
            for n in nodes:
                enriched.append(
                    LineageGraphNode(
                        id=n.id,
                        label=n.label,
                        type=n.type,
                        source_id=n.source_id,
                        parent_id=n.parent_id,
                        ordinal_position=n.ordinal_position,
                        distance=n.distance if n.distance is not None else dist.get(str(n.id)),
                        source_name=n.source_name,
                        primary_tag=getattr(n, "primary_tag", None),
                    )
                )
            nodes = enriched

        # enrich primary_tag and source_name if db_session available
        if self.db_session and nodes:
            table_ids = [n.id for n in nodes if n.type == "table"]
            repo = TableRepository(self.db_session)
            table_map = await repo.get_tables_with_primary_tags([uuid.UUID(t) for t in table_ids]) if table_ids else {}
            enriched_nodes = []
            for n in nodes:
                extra = table_map.get(str(n.id)) or {}
                enriched_nodes.append(
                    LineageGraphNode(
                        id=n.id,
                        label=n.label,
                        type=n.type,
                        source_id=n.source_id or extra.get("source_id"),
                        parent_id=n.parent_id,
                        ordinal_position=n.ordinal_position,
                        primary_tag=extra.get("primary_tag"),
                        distance=n.distance if n.distance is not None else (0 if str(n.id) == record.get("root_id") else None),
                        source_name=extra.get("source_name"),
                    )
                )
            nodes = enriched_nodes

        return LineageGraphResponse(
            root_id=root_id or "",
            nodes=nodes,
            edges=edges,
        )

    async def _root_only_graph(self, table_id: str) -> LineageGraphResponse:
        """Return only the focal table node when Neo4j has no data (e.g., no lineage yet)."""
        if not self.db_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
        repo = TableRepository(self.db_session)
        try:
            table_uuid = uuid.UUID(table_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

        table_map = await repo.get_tables_with_primary_tags([table_uuid])
        table_info = table_map.get(str(table_id))
        if not table_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

        node = LineageGraphNode(
            id=str(table_id),
            label=table_info.get("name"),
            type="table",
            source_id=table_info.get("source_id"),
            source_name=table_info.get("source_name"),
            primary_tag=table_info.get("primary_tag"),
            distance=0,
        )
        return LineageGraphResponse(root_id=str(table_id), nodes=[node], edges=[])
