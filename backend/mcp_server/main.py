from __future__ import annotations

from typing import Optional, AsyncGenerator

from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.graph.client import get_neo4j_driver
from app.services.mcp_tools import LineageTools
from app.db import SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with SessionLocal() as session:
        yield session


async def get_tools(session: AsyncSession) -> LineageTools:
    """Get LineageTools instance with session and neo4j driver."""
    neo4j_driver: AsyncDriver = get_neo4j_driver()
    return LineageTools(neo4j_driver, session, redis=None)


mcp = FastMCP()


@mcp.tool(description="Search tables by fuzzy name matching. Returns list of matching tables with id, name, and basic info. Use when user asks '找表', '搜索表', '有哪些表' WITHOUT specifying exact table name. Example: search_tables(keyword='SECU', limit=10)")
async def search_tables(keyword: str, limit: int = 20):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.search_tables(keyword, limit)


@mcp.tool(description="Get complete table information including all fields, tags, and metadata. Parameter table_id can be either UUID or exact table name (case-insensitive). Use when user asks '表详情', '这个表有什么字段', '表的结构'. IMPORTANT: If user provides exact table name (e.g., 'SECUMAIN的详细信息'), use it DIRECTLY. Example: get_table_details(table_id='SECUMAIN')")
async def get_table_details(table_id: str):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.get_table_details(table_id)


@mcp.tool(description="Search fields by fuzzy name matching across all tables. Returns list of matching fields with field name, table name, and data type. Use when user asks '找字段', '搜索字段', '有哪些字段' WITHOUT specifying exact field name. Example: search_fields(keyword='user_id', limit=10)")
async def search_fields(keyword: str, limit: int = 20):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.search_fields(keyword, limit)


@mcp.tool(description="Get upstream lineage graph - tables that feed data INTO this table. Use when user asks '上游', '数据来源', '依赖哪些表'. IMPORTANT: If user provides table name, use it DIRECTLY. depth: 1-5 (recommended ≤3 for performance). Example: get_upstream_lineage(table_id='SECUMAIN', depth=2)")
async def get_upstream_lineage(table_id: str, depth: int = 3):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.get_upstream_lineage(table_id, depth)


@mcp.tool(description="Get downstream lineage graph - tables that this table feeds data INTO. Use when user asks '下游', '影响哪些表', '被哪些表使用'. IMPORTANT: If user provides table name, use it DIRECTLY. depth: 1-5 (recommended ≤3 for performance). Returns graph with nodes and edges. Example: get_downstream_lineage(table_id='SECUMAIN', depth=2)")
async def get_downstream_lineage(table_id: str, depth: int = 3):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.get_downstream_lineage(table_id, depth)


@mcp.tool(description="Find the lineage connection path between two tables (from start to end). Use when user asks 'A到B的血缘路径', '如何连接', '两个表的关系'. Returns all possible paths. Example: find_lineage_path(start_id='SECUMAIN', end_id='TRADE_INFO', max_depth=10)")
async def find_lineage_path(start_id: str, end_id: str, max_depth: int = 10):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.find_lineage_path(start_id, end_id, max_depth)


@mcp.tool(description="Calculate business impact scope (爆炸半径) - how many tables/business domains would be affected if this table changes. Use when user asks '影响范围', '爆炸半径', '改这个表会影响什么'. IMPORTANT: If user provides table name, use it DIRECTLY. direction: 'downstream' (default, what this table affects) or 'upstream' (what affects this table). granularity: 'table' (default) or 'field'. Returns affected table count, business domain breakdown, and severity assessment. Example: calculate_blast_radius(table_id='SECUMAIN', direction='downstream', depth=5, granularity='table')")
async def calculate_blast_radius(table_id: str, direction: str = "downstream", depth: int = 5, granularity: str = "table"):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.calculate_blast_radius(table_id, direction, depth, granularity)


@mcp.tool(description="Detect circular dependencies (环路检测) in lineage graph starting from this table. Use when user asks '环路', '循环依赖', '是否有环'. IMPORTANT: If user provides table name, use it DIRECTLY. Returns list of detected cycles with participating tables. Example: detect_cycles(table_id='SECUMAIN', depth=10)")
async def detect_cycles(table_id: str, depth: int = 10):
    async for session in get_session():
        tools = await get_tools(session)
        return await tools.detect_cycles(table_id, depth)


if __name__ == "__main__":
    mcp.run()
