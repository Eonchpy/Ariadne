from __future__ import annotations

import uuid
from typing import Any, Optional
import json
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_client import LLMClient
from app.repositories.conversation_repo import ConversationRepository, MessageRepository
from app.schemas.ai import AIMessage, AIChatResponse


class AIService:
    def __init__(self, session: AsyncSession, llm_client: Optional[LLMClient] = None):
        self.session = session
        self.llm = llm_client or LLMClient()
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)

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
