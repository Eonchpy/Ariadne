#!/usr/bin/env python
"""Test MCP tools schema conversion"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_mcp_tools():
    root = Path(__file__).parent
    server_script = root / "mcp_server" / "main.py"

    command = sys.executable
    args = [str(server_script)]

    transport = StdioTransport(command=command, args=args, env={})

    async with Client(transport=transport) as client:
        tools = await client.list_tools()

        print(f"✅ Found {len(tools)} tools\n")

        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"  Description: {tool.description}")
            print(f"  Has inputSchema: {hasattr(tool, 'inputSchema')}")
            if hasattr(tool, 'inputSchema'):
                print(f"  InputSchema: {tool.inputSchema}")
            print()


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
