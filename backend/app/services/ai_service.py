from __future__ import annotations

import uuid
from typing import Any, Optional
import json
import asyncio
import time
import sys
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.llm_client import LLMClient
from app.repositories.conversation_repo import ConversationRepository, MessageRepository
from app.schemas.ai import AIMessage, AIChatResponse
from app.services.mcp_tools import LineageTools
from app.graph.client import get_neo4j_driver
from fastmcp import Client as MCPClient
from fastmcp.client.transports import StdioTransport


class AIService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: Optional[LLMClient] = None,
        neo4j_driver=None,
        redis=None,
    ):
        self.session = session
        self.llm: Optional[LLMClient] = llm_client
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)
        # Optional direct tool access (bypassing MCP server for now)
        self.neo4j_driver = neo4j_driver
        self.redis = redis
        self.mcp_client: Optional[MCPClient] = None

    async def _ensure_mcp(self):
        if self.mcp_client:
            return self.mcp_client
        # Start MCP server as subprocess (fastmcp)
        root = Path(__file__).resolve().parents[2]
        server_script = root / "mcp_server" / "main.py"
        env = os.environ.copy()
        # ensure project root on PYTHONPATH
        env["PYTHONPATH"] = f"{root}:{env.get('PYTHONPATH','')}"

        # StdioTransport requires command (str) and args (list[str])
        command = sys.executable
        args = [str(server_script)]

        transport = StdioTransport(command=command, args=args, env=env)
        self.mcp_client = MCPClient(transport=transport)
        # Client is an async context manager, call __aenter__ to initialize
        await self.mcp_client.__aenter__()
        return self.mcp_client

    async def get_mcp_tools_schema(self) -> list[dict]:
        """Get tools schema from MCP server and convert to OpenAI function calling format."""
        mcp = await self._ensure_mcp()
        # List tools from MCP server (returns list[Tool] directly)
        tools_list = await mcp.list_tools()

        openai_tools = []
        for tool in tools_list:
            # Convert MCP tool schema to OpenAI function calling format
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"MCP tool: {tool.name}",
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            })

        return openai_tools

    def _get_llm(self) -> LLMClient:
        if self.llm is None:
            # Lazy init to avoid startup failure when LLM credentials are absent
            self.llm = LLMClient()
        return self.llm

    async def ensure_conversation(self, user_id: uuid.UUID, conversation_id: Optional[str]) -> uuid.UUID:
        if conversation_id:
            conv = await self.conv_repo.get(uuid.UUID(conversation_id), user_id)
            if conv:
                return conv.id
        conv = await self.conv_repo.create(user_id=user_id, title="")
        await self.session.commit()
        return conv.id

    async def append_message(
        self, conv_id: uuid.UUID, role: str, type_: str, content: str, metadata: Optional[dict[str, Any]] = None
    ):
        await self.msg_repo.add(conv_id, role, type_, content, metadata or {})
        await self.session.commit()

    async def simple_echo(self, user_id: uuid.UUID, query: str, conversation_id: Optional[str]) -> AIChatResponse:
        conv_id = await self.ensure_conversation(user_id, conversation_id)
        await self.append_message(conv_id, "user", "text", query, {})
        reply = "AI assistant is not yet implemented. Received: " + query
        await self.append_message(conv_id, "assistant", "text", reply, {})
        return AIChatResponse(
            messages=[AIMessage(role="assistant", type="text", content=reply)],
            suggested_questions=[
                "查看某个表的下游有哪些？",
                "帮我计算 blast radius",
                "是否存在血缘环路？",
            ],
        )

    async def sse_placeholder(self, query: str):
        yield f"event: status\ndata: {json.dumps({'message': 'Processing request...', 'tool': 'llm', 'progress': 0})}\n\n"
        await asyncio.sleep(0.05)
        msg = {"type": "text", "content": "AI assistant is not yet implemented. Received: " + query}
        yield f"event: data\ndata: {json.dumps(msg)}\n\n"
        sugg = {"type": "suggestions", "content": ["查看某个表的下游有哪些？", "帮我计算 blast radius", "是否存在血缘环路？"]}
        yield f"event: data\ndata: {json.dumps(sugg)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Done', 'tool': 'llm', 'progress': 100})}\n\n"

    async def run_llm_with_tools(self, messages: list[dict], tools: list[dict], stream: bool = True):
        # Orchestrator:
        # 1) Ask LLM; if it replies with plain text (no tool_calls), return that directly.
        # 2) If tool_calls present, execute tools (via MCP), then ask LLM to summarize tool results.
        start = time.perf_counter()
        result_summary = None
        tool_calls = []

        llm = self._get_llm()
        completion = await llm.achat(messages, tools=tools, stream=False)
        choice_msg = completion.model_dump().get("choices", [])[0].get("message", {}) or {}
        tool_calls = choice_msg.get("tool_calls") or []

        # If no tool calls, return the assistant content directly
        if not tool_calls:
            result_summary = choice_msg.get("content")
            duration_ms = (time.perf_counter() - start) * 1000
            return result_summary, [], duration_ms

        status_events = []
        if tool_calls:
            status_events.append({"message": "Calling tool...", "tool": tool_calls[0].get("function", {}).get("name"), "progress": 30})
            # Append assistant message containing tool_calls per OpenAI spec
            messages.append(
                {
                    "role": "assistant",
                    "content": choice_msg.get("content"),
                    "tool_calls": tool_calls,
                }
            )
            mcp = await self._ensure_mcp()
            for tc in tool_calls:
                fname = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"] or "{}")
                try:
                    tool_result = await mcp.call_tool(fname, **args)
                except Exception:
                    # fallback to direct if MCP fails
                    tool_result = await self.call_tool_direct(fname, args)
                # Append tool result message (role=tool) referencing tool_call_id per spec
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result),
                    }
                )
            status_events.append({"message": "Summarizing...", "tool": "llm", "progress": 70})
            final = await llm.achat(messages, stream=False)
            result_summary = final.model_dump().get("choices", [])[0].get("message", {}).get("content")
        duration_ms = (time.perf_counter() - start) * 1000
        return result_summary, status_events, duration_ms

    async def call_tool_direct(self, name: str, params: dict[str, any]):
        """Direct call to lineage tools (bypassing MCP server)."""
        if not self.neo4j_driver:
            self.neo4j_driver = get_neo4j_driver()
        tools = LineageTools(self.neo4j_driver, self.session, redis=self.redis)
        if name == "search_tables":
            return await tools.search_tables(**params)
        if name == "search_fields":
            return await tools.search_fields(**params)
        if name == "get_table_details":
            return await tools.get_table_details(**params)
        if name == "get_upstream_lineage":
            return await tools.get_upstream_lineage(**params)
        if name == "get_downstream_lineage":
            return await tools.get_downstream_lineage(**params)
        if name == "find_lineage_path":
            return await tools.find_lineage_path(**params)
        if name == "calculate_blast_radius":
            return await tools.calculate_blast_radius(**params)
        if name == "detect_cycles":
            return await tools.detect_cycles(**params)
        raise ValueError(f"Unknown tool: {name}")
