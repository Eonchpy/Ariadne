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
    PathsResponse,
    CycleListResponse,
    ImpactAnalysisResponse,
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

    async def delete_lineage(self, rel_id: str) -> None:
        try:
            rel_int = int(rel_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid relationship id")
        async with self.driver.session() as session:
            result = await session.run(queries.DELETE_LINEAGE, rel_id=rel_int)
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

    async def find_paths(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 20,
        shortest_only: bool = False,
    ) -> PathsResponse:
        async with self.driver.session() as session:
            query = queries.SHORTEST_PATHS if shortest_only else queries.ALL_PATHS
            result = await session.run(query, start_id=start_id, end_id=end_id, max_depth=max_depth)
            paths = []
            nodes_seen = {}
            edges_seen = {}
            async for record in result:
                path = record["path"]
                if not path:
                    continue
                nodes_in_path = list(path.nodes)
                rels_in_path = list(path.relationships)
                paths.append(
                    {"path": [n["id"] for n in nodes_in_path if "id" in n], "length": len(nodes_in_path) - 1}
                )
                for idx, n in enumerate(nodes_in_path):
                    nid = n.get("id")
                    if nid and nid not in nodes_seen:
                        # Preserve labels for type detection and attach distance from start
                        props = dict(n)
                        props["labels"] = list(getattr(n, "labels", []))
                        props["distance"] = idx
                        props.setdefault("id", nid)
                        nodes_seen[nid] = props
                    for r in rels_in_path:
                        rid = str(r.id)
                        if rid not in edges_seen:
                            edges_seen[rid] = {
                                "id": rid,
                            "from": r.start_node["id"],
                            "to": r.end_node["id"],
                            "lineage_source": r.get("lineage_source"),
                            "confidence": r.get("confidence"),
                            "rel_type": type(r).__name__ if hasattr(r, "__class__") else None,
                        }

        nodes = await self._convert_nodes(list(nodes_seen.values()))
        edges = self._convert_edges(list(edges_seen.values()))
        return PathsResponse(
            nodes=nodes,
            edges=edges,
            paths=[{"path": p["path"], "length": p.get("length")} for p in paths],
        )

    async def find_cycles(self, table_id: str | None = None, max_depth: int = 10) -> CycleListResponse:
        async with self.driver.session() as session:
            result = await session.run(queries.CYCLES_BY_TABLE, table_id=table_id, max_depth=max_depth)
            cycles = []
            nodes_seen = {}
            edges_seen = {}
            async for record in result:
                path = record["path"]
                if not path:
                    continue
                nodes_in_path = list(path.nodes)
                rels_in_path = list(path.relationships)
                cycles.append([n["id"] for n in nodes_in_path if "id" in n])
                for n in nodes_in_path:
                    nid = n.get("id")
                    if nid and nid not in nodes_seen:
                        nodes_seen[nid] = n
                for r in rels_in_path:
                    rid = str(r.id)
                    if rid not in edges_seen:
                        edges_seen[rid] = {
                            "id": rid,
                            "from": r.start_node["id"],
                            "to": r.end_node["id"],
                            "lineage_source": r.get("lineage_source"),
                            "confidence": r.get("confidence"),
                            "rel_type": type(r).__name__ if hasattr(r, "__class__") else None,
                        }

        nodes = await self._convert_nodes(list(nodes_seen.values()))
        edges = self._convert_edges(list(edges_seen.values()))
        return CycleListResponse(cycles=cycles, nodes=nodes, edges=edges)

    async def impact_analysis(self, node_id: str, direction: str = "downstream", depth: int = 5) -> ImpactAnalysisResponse:
        # reuse get_graph with direction; gather impacted nodes list
        graph = await self.get_graph(table_id=node_id, depth=depth, direction=direction)
        impacted = []
        for n in graph.nodes:
            if str(n.id) == graph.root_id:
                continue
            impacted.append(
                {
                    "id": n.id,
                    "distance": n.distance,
                    "type": n.type,
                    "primary_tag": getattr(n, "primary_tag", None),
                    "source_name": n.source_name,
                }
            )
        return ImpactAnalysisResponse(
            root_id=graph.root_id,
            direction=direction,
            depth=depth,
            nodes=graph.nodes,
            edges=graph.edges,
            impacted=impacted,
        )

    async def blast_radius(
        self,
        table_id: str,
        direction: str = "downstream",
        depth: int = 5,
        granularity: str = "table",
    ):
        # Get graph in the desired direction/depth
        graph = await self.get_graph(table_id=table_id, depth=depth, direction=direction)

        # Deduplicate tables/fields and capture min distance
        table_nodes = [n for n in graph.nodes if n.type == "table" and str(n.id) != graph.root_id]
        field_nodes = [n for n in graph.nodes if n.type == "field"]

        table_distance: dict[str, int] = {}
        for n in table_nodes:
            dist = n.distance or 0
            if str(n.id) not in table_distance or dist < table_distance[str(n.id)]:
                table_distance[str(n.id)] = dist
        field_distance: dict[str, int] = {}
        for f in field_nodes:
            dist = f.distance or 0
            if str(f.id) not in field_distance or dist < field_distance[str(f.id)]:
                field_distance[str(f.id)] = dist

        total_tables = len(table_distance)
        total_fields = len(field_distance)
        max_depth_reached = max(table_distance.values()) if table_distance else 0

        def severity_for(count: int) -> str:
            if count >= 10:
                return "high"
            if count >= 5:
                return "medium"
            return "low"

        # Group by primary_tag
        domain_groups: dict[str, dict] = {}
        for n in table_nodes:
            pid = None
            pname = None
            ppath = None
            if hasattr(n, "primary_tag") and n.primary_tag:
                pid = n.primary_tag.get("id")
                pname = n.primary_tag.get("name")
                ppath = n.primary_tag.get("path")
            key = str(pid) if pid else f"__no_tag__:{n.id}"
            if key not in domain_groups:
                domain_groups[key] = {
                    "tag_id": pid,
                    "tag_name": pname,
                    "tag_path": ppath,
                    "tables": [],
                }
            domain_groups[key]["tables"].append({"id": str(n.id), "name": n.label, "distance": n.distance})

        # Build depth map (hop -> table count)
        depth_map: dict[int, int] = {}
        for dist in table_distance.values():
            if dist <= 0:
                continue
            depth_map[dist] = depth_map.get(dist, 0) + 1

        groups_out = []
        for g in domain_groups.values():
            tables = g["tables"]
            count = len(tables)
            sev = severity_for(count)
            # sort sample by distance then name
            tables_sorted = sorted(tables, key=lambda t: (t.get("distance") or 0, t.get("name") or ""))[:5]
            groups_out.append(
                {
                    "tag_id": g["tag_id"],
                    "tag_name": g["tag_name"],
                    "tag_path": g["tag_path"],
                    "table_count": count,
                    "severity": sev,
                    "sample_tables": tables_sorted,
                }
            )

        # Sort groups: severity high>medium>low, then table_count desc
        sev_order = {"high": 0, "medium": 1, "low": 2}
        groups_out = sorted(groups_out, key=lambda g: (sev_order.get(g["severity"], 3), -g["table_count"]))

        overall_sev = severity_for(total_tables)

        from app.schemas.lineage import BlastRadiusResponse  # local import to avoid cycle

        return BlastRadiusResponse(
            root_id=table_id,
            direction=direction,
            depth=depth,
            granularity=granularity,
            total_impacted_tables=total_tables,
            total_impacted_fields=total_fields if granularity == "field" else 0,
            total_impacted_domains=len(groups_out),
            max_depth_reached=max_depth_reached,
            severity_level=overall_sev,
            domain_groups=groups_out,
            depth_map=depth_map,
        )

    async def quality_check(self, table_id: str, max_depth: int = 10):
        async with self.driver.session() as session:
            result = await session.run(queries.QUALITY_CHECK_CYCLES, table_id=table_id, max_depth=max_depth)
            paths_raw: list[list[str]] = []
            nodes_seen: dict[str, Any] = {}
            async for record in result:
                path = record["path"]
                if not path:
                    continue
                node_ids = []
                for n in path.nodes:
                    nid = n.get("id")
                    if nid:
                        node_ids.append(nid)
                        if nid not in nodes_seen:
                            nodes_seen[nid] = n
                if node_ids:
                    paths_raw.append(node_ids)

        # enrich nodes
        nodes_enriched = await self._convert_nodes(list(nodes_seen.values()))
        node_map = {str(n.id): n for n in nodes_enriched}

        def to_qc_node(n: LineageGraphNode):
            primary_path = None
            if n.primary_tag:
                primary_path = n.primary_tag.get("path")
            return {
                "id": str(n.id),
                "name": n.label,
                "primary_tag_path": primary_path,
                "source_name": n.source_name,
                "type": n.type,
            }

        cycles_out: list[list[dict[str, Any]]] = []
        seen_set = set()
        for ids in paths_raw:
            key = tuple(ids)
            if key in seen_set:
                continue
            seen_set.add(key)
            cycle_nodes = []
            for nid in ids:
                if nid in node_map:
                    cycle_nodes.append(to_qc_node(node_map[nid]))
            if cycle_nodes:
                cycles_out.append(cycle_nodes)

        has_cycles = len(cycles_out) > 0
        severity = "high" if has_cycles else "low"
        from datetime import datetime, timezone
        from app.schemas.lineage import QualityCheckResponse  # local import

        return QualityCheckResponse(
            has_cycles=has_cycles,
            cycles=cycles_out,
            severity_level=severity,
            issue_count=len(cycles_out),
            audit_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    async def _convert_nodes(self, raw_nodes: list[Any]) -> list[LineageGraphNode]:
        nodes: list[LineageGraphNode] = []
        for node in raw_nodes:
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
            parent_id = props.get("table_id")
            ordinal_position = props.get("ordinal_position")
            distance = props.get("depth") or props.get("distance")
            node_type = "table"
            if "Field" in labels:
                node_type = "field"
            elif "Table" in labels:
                node_type = "table"
            elif props.get("table_id"):
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
                        distance=distance,
                    )
                )
        if self.db_session and nodes:
            table_ids = [n.id for n in nodes if n.type == "table"]
            repo = TableRepository(self.db_session)
            table_map = await repo.get_tables_with_primary_tags([uuid.UUID(t) for t in table_ids]) if table_ids else {}
            enriched = []
            for n in nodes:
                extra = table_map.get(str(n.id)) or {}
                enriched.append(
                    LineageGraphNode(
                        id=n.id,
                        label=n.label,
                        type=n.type,
                        source_id=n.source_id or extra.get("source_id"),
                        parent_id=n.parent_id,
                        ordinal_position=n.ordinal_position,
                        distance=n.distance,
                        primary_tag=extra.get("primary_tag"),
                        source_name=extra.get("source_name"),
                    )
                )
            nodes = enriched
        return nodes

    def _convert_edges(self, raw_edges: list[Any]) -> list[LineageGraphEdge]:
        edges: list[LineageGraphEdge] = []
        for rel in raw_edges or []:
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
        return edges

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
