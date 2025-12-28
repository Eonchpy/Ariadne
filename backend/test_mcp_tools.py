#!/usr/bin/env python
"""Test script to verify MCP tool registration"""
from __future__ import annotations

import asyncio
from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from neo4j import AsyncDriver

from app.config import settings
from app.graph.client import get_neo4j_driver
from app.services.mcp_tools import LineageTools
from app.db import engine

# Create MCP instance
mcp = FastMCP()

# Register all tools (same as in main.py)
@mcp.tool(description="Search tables by name (fuzzy match). Params: keyword (str), limit (int, default 20).")
async def search_tables(keyword: str, limit: int = 20):
    pass

@mcp.tool(description="Get table details by ID, including fields/tags.")
async def get_table_details(table_id: str):
    pass

@mcp.tool(description="Search fields by name (fuzzy match). Params: keyword (str), limit (int, default 20).")
async def search_fields(keyword: str, limit: int = 20):
    pass

@mcp.tool(description="Get upstream lineage graph for a table. Params: table_id (UUID), depth (<=5 recommended).")
async def get_upstream_lineage(table_id: str, depth: int = 3):
    pass

@mcp.tool(description="Get downstream lineage graph for a table. Params: table_id (UUID), depth (<=5 recommended).")
async def get_downstream_lineage(table_id: str, depth: int = 3):
    pass

@mcp.tool(description="Find paths between two nodes (table/field). Params: start_id, end_id, max_depth (<=10).")
async def find_lineage_path(start_id: str, end_id: str, max_depth: int = 10):
    pass

@mcp.tool(description="Calculate blast radius for a table. Params: table_id, direction (upstream/downstream), depth (<=5), granularity (table/field).")
async def calculate_blast_radius(table_id: str, direction: str = "downstream", depth: int = 5, granularity: str = "table"):
    pass

@mcp.tool(description="Detect lineage cycles for a table. Params: table_id, depth (<=10).")
async def detect_cycles(table_id: str, depth: int = 10):
    pass


async def main():
    # Check registered tools
    tools_dict = await mcp.get_tools()
    print(f"✅ Total tools registered: {len(tools_dict)}")
    print("\nRegistered tools:")
    for name, tool in tools_dict.items():
        print(f"  - {name}: {tool.description}")

    # Verify expected count
    expected_tools = [
        "search_tables",
        "get_table_details",
        "search_fields",
        "get_upstream_lineage",
        "get_downstream_lineage",
        "find_lineage_path",
        "calculate_blast_radius",
        "detect_cycles"
    ]

    actual_names = list(tools_dict.keys())
    missing = set(expected_tools) - set(actual_names)
    extra = set(actual_names) - set(expected_tools)

    if missing:
        print(f"\n❌ Missing tools: {missing}")
    elif extra:
        print(f"\n⚠️  Extra tools: {extra}")
    else:
        print(f"\n✅ All {len(expected_tools)} expected tools are registered correctly!")


if __name__ == "__main__":
    asyncio.run(main())
