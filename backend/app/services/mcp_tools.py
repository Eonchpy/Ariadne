from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver
from fastapi import HTTPException

from app.services.lineage_service import LineageService
from app.repositories.table_repo import TableRepository
from app.repositories.field_repo import FieldRepository


class LineageTools:
    def __init__(self, neo4j_driver: AsyncDriver, db_session: AsyncSession, redis=None):
        self.neo4j_driver = neo4j_driver
        self.db_session = db_session
        self.redis = redis
        self.lineage_service = LineageService(neo4j_driver, db_session=db_session, redis=redis)
        self.table_repo = TableRepository(db_session)
        self.field_repo = FieldRepository(db_session)

    async def _resolve_table_id(self, table_ref: str) -> str:
        """Accept UUID string or table name (case-insensitive). Returns UUID string or raises HTTPException."""
        # UUID-looking
        if len(table_ref) == 36 and table_ref.count("-") == 4:
            return table_ref
        # exact name
        table = await self.table_repo.get_by_name_exact(table_ref)
        if table:
            return str(table.id)
        # normalized name (lowercase)
        table = await self.table_repo.get_by_name_normalized(table_ref)
        if table:
            return str(table.id)
        raise HTTPException(status_code=404, detail="table not found")

    async def search_tables(self, keyword: str, limit: int = 20):
        if not keyword:
            raise HTTPException(status_code=400, detail="keyword is required")
        limit = min(max(limit, 1), 50)
        tables = await self.table_repo.search_by_name(keyword, limit=limit)
        data = []
        for t in tables:
            primary_tag = None
            if getattr(t, "primary_tag_id", None):
                primary_tag = {"id": str(t.primary_tag_id)}
            data.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "qualified_name": t.qualified_name,
                    "primary_tag": primary_tag,
                    "source_id": str(t.source_id) if t.source_id else None,
                }
            )
        return {"summary": {"count": len(data)}, "data": data}

    async def search_fields(self, keyword: str, limit: int = 20):
        if not keyword:
            raise HTTPException(status_code=400, detail="keyword is required")
        limit = min(max(limit, 1), 50)
        fields = await self.field_repo.search_by_name(keyword, limit=limit)
        data = []
        for f in fields:
            data.append(
                {
                    "id": str(f.id),
                    "name": f.name,
                    "table_id": str(f.table_id),
                    "data_type": f.data_type,
                    "ordinal_position": getattr(f, "ordinal_position", None),
                }
            )
        return {"summary": {"count": len(data)}, "data": data}

    async def get_table_details(self, table_id: str):
        table_id = await self._resolve_table_id(table_id)
        t = await self.table_repo.get(table_id)
        if not t:
            return {"error": "table not found"}
        fields = await self.field_repo.list_by_table(table_id)
        primary_tag = None
        if getattr(t, "primary_tag_id", None):
            primary_tag = {"id": str(t.primary_tag_id)}
        return {
            "summary": {"field_count": len(fields)},
            "id": str(t.id),
            "name": t.name,
            "qualified_name": t.qualified_name,
            "primary_tag": primary_tag,
            "source_id": str(t.source_id) if t.source_id else None,
            "tags": t.tags or [],
            "fields": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "data_type": f.data_type,
                    "ordinal_position": getattr(f, "ordinal_position", None),
                    "is_primary_key": f.is_primary_key,
                }
                for f in fields
            ],
        }

    async def get_upstream_lineage(self, table_id: str, depth: int = 3):
        depth = min(max(depth, 1), 5)
        table_id = await self._resolve_table_id(table_id)
        graph = await self.lineage_service.get_upstream(table_id, depth)
        return {"summary": {"nodes": len(graph.nodes), "edges": len(graph.edges)}, "data": graph.model_dump()}

    async def get_downstream_lineage(self, table_id: str, depth: int = 3):
        depth = min(max(depth, 1), 5)
        table_id = await self._resolve_table_id(table_id)
        graph = await self.lineage_service.get_downstream(table_id, depth)
        return {"summary": {"nodes": len(graph.nodes), "edges": len(graph.edges)}, "data": graph.model_dump()}

    async def find_lineage_path(self, start_id: str, end_id: str, max_depth: int = 10):
        max_depth = min(max(max_depth, 1), 10)
        paths = await self.lineage_service.find_paths(start_id=start_id, end_id=end_id, max_depth=max_depth)
        return {"summary": {"path_count": len(paths.paths)}, "data": paths.model_dump()}

    async def calculate_blast_radius(self, table_id: str, direction: str = "downstream", depth: int = 5, granularity: str = "table"):
        depth = min(max(depth, 1), 5)
        table_id = await self._resolve_table_id(table_id)
        res = await self.lineage_service.blast_radius(table_id=table_id, direction=direction, depth=depth, granularity=granularity)
        return {
            "summary": {
                "total_impacted_tables": res.total_impacted_tables,
                "total_impacted_domains": res.total_impacted_domains,
                "max_depth_reached": res.max_depth_reached,
                "severity_level": res.severity_level,
            },
            "data": res.model_dump(),
        }

    async def detect_cycles(self, table_id: str, depth: int = 10):
        depth = min(max(depth, 1), 10)
        target_id = await self._resolve_table_id(table_id)
        res = await self.lineage_service.quality_check(table_id=target_id, max_depth=depth)
        return {
            "summary": {"has_cycles": res.has_cycles, "issue_count": res.issue_count},
            "data": res.model_dump(),
        }
