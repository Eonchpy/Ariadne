from __future__ import annotations

import uuid
from typing import Any, Optional
import json
import re
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
        self.table_repo = None  # lazy init for label resolution

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
        # 2) If tool_calls present (or DSML-like pseudo tool_calls), execute tools, then ask LLM to summarize tool results.
        start = time.perf_counter()
        result_summary = None
        tool_calls = []
        actions: list[dict[str, Any]] = []

        llm = self._get_llm()
        completion = await llm.achat(messages, tools=tools, stream=False)
        choice_msg = completion.model_dump().get("choices", [])[0].get("message", {}) or {}
        tool_calls = choice_msg.get("tool_calls") or []

        # If no tool calls, return the assistant content directly (unless DSML pseudo-calls detected)
        if not tool_calls:
            # Try to parse DSML-like pseudo calls, e.g. <｜DSML｜function_calls>...
            pseudo_calls = self._parse_dsml_calls(choice_msg.get("content") or "")
            if pseudo_calls:
                status_events = [{"message": "Calling tool...", "tool": pseudo_calls[0][0], "progress": 30}]
                # Append a synthetic assistant message carrying pseudo tool_calls to keep convo continuity
                messages.append({"role": "assistant", "content": choice_msg.get("content")})
                for fname, args in pseudo_calls:
                    try:
                        tool_result = await self.call_tool_direct(fname, args)
                    except Exception:
                        tool_result = {"error": f"tool {fname} failed"}
                    await self._append_actions(fname, args, tool_result, actions)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": fname,
                            "content": json.dumps(tool_result),
                        }
                    )
                status_events.append({"message": "Summarizing...", "tool": "llm", "progress": 70})
                final = await llm.achat(messages, stream=False)
                result_summary = final.model_dump().get("choices", [])[0].get("message", {}).get("content")
                result_summary = self._strip_actions_block(result_summary)
                duration_ms = (time.perf_counter() - start) * 1000
                return result_summary, status_events, actions, duration_ms

            # No tool calls and no DSML pseudo calls: return text as-is
            result_summary = choice_msg.get("content")
            result_summary = self._strip_actions_block(result_summary)
            duration_ms = (time.perf_counter() - start) * 1000
            return result_summary, [], actions, duration_ms

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

                await self._append_actions(fname, args, tool_result, actions)

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
        result_summary = self._strip_actions_block(result_summary)
        duration_ms = (time.perf_counter() - start) * 1000
        return result_summary, status_events, actions, duration_ms

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

    def _parse_dsml_calls(self, content: str) -> list[tuple[str, dict[str, Any]]]:
        """Very simple parser for <｜DSML｜function_calls> ... <｜DSML｜invoke name=\"...\"> ...</｜DSML｜invoke>"""
        calls: list[tuple[str, dict[str, Any]]] = []
        if "<｜DSML｜" not in content:
            return calls
        # Split invocations
        invocations = re.findall(r"<｜DSML｜invoke name=\"([^\"]+)\">(.*?)</｜DSML｜invoke>", content, re.S)
        for fname, body in invocations:
            args: dict[str, Any] = {}
            params = re.findall(r"<｜DSML｜parameter name=\"([^\"]+)\"[^>]*>(.*?)</｜DSML｜parameter>", body, re.S)
            for pname, pval in params:
                args[pname] = pval.strip()
            calls.append((fname, args))
        return calls

    async def _append_actions(self, fname: str, args: dict[str, Any], tool_result: Any, actions: list[dict[str, Any]]):
        if fname in {"get_table_details", "get_upstream_lineage", "get_downstream_lineage", "calculate_blast_radius", "detect_cycles"}:
            table_id = self._extract_table_id(args, tool_result)
            label = None
            if isinstance(tool_result, dict):
                label = tool_result.get("name") or (tool_result.get("data") or {}).get("name")
            if table_id:
                # If label missing, try to resolve table name from DB
                if not label:
                    try:
                        if self.table_repo is None:
                            from app.repositories.table_repo import TableRepository
                            self.table_repo = TableRepository(self.session)
                        tbl = await self.table_repo.get(table_id)
                        if tbl and getattr(tbl, "name", None):
                            label = tbl.name
                    except Exception:
                        pass
                actions.append(
                    {
                        "id": f"act_{len(actions)+1}",
                        "type": "focus_node",
                        "label": label or str(table_id),
                        "payload": {
                            "id": str(table_id),
                            "graph_type": "lineage",
                            "direction": args.get("direction"),
                            "force_extract": True,
                        },
                    }
                )
        elif fname == "find_lineage_path":
            start_id = args.get("start_id")
            end_id = args.get("end_id")
            if start_id and end_id:
                nodes = []
                edges = []
                if isinstance(tool_result, dict):
                    data = tool_result.get("data") or {}
                    nodes = data.get("nodes") or []
                    edges = data.get("edges") or []
                actions.append(
                    {
                        "id": f"act_{len(actions)+1}",
                        "type": "trace_path",
                        "label": f"path: {start_id} -> {end_id}",
                        "payload": {
                            "nodes": nodes or [{"id": start_id}, {"id": end_id}],
                            "edges": edges or [],
                            "color": "blue",
                            "force_extract": True,
                        },
                    }
                )

    def _extract_table_id(self, args: dict[str, Any], tool_result: Any) -> Optional[str]:
        # Prefer tool_result data if present
        if isinstance(tool_result, dict):
            if tool_result.get("id"):
                return str(tool_result["id"])
            data = tool_result.get("data") or {}
            if isinstance(data, dict):
                if data.get("root_id"):
                    return str(data["root_id"])
                if data.get("id"):
                    return str(data["id"])
        # Fallback to args
        return args.get("table_id") or args.get("table_ref")

    def _strip_actions_block(self, content: Optional[str]) -> Optional[str]:
        """Strip unwanted blocks from LLM output (actions, DSML pseudo-calls)."""
        if not content:
            return content

        # Strip <actions> blocks
        if "<actions>" in content:
            content = re.sub(r"<actions>.*?</actions>", "", content, flags=re.S)

        # Strip DSML function_calls blocks (hallucinated tool calls)
        if "<｜DSML｜" in content:
            content = re.sub(r"<｜DSML｜function_calls>.*?</｜DSML｜function_calls>", "", content, flags=re.S)
            # Also strip standalone DSML invocations
            content = re.sub(r"<｜DSML｜invoke.*?</｜DSML｜invoke>", "", content, flags=re.S)

        return content.strip()
