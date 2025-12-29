from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api import deps
from app.schemas.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse, AIMessage
from app.schemas.conversation import ConversationCreate, ConversationListItem, ConversationDetail, ConversationMessage
from app.core.llm_client import LLMClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db_session
from app.repositories.conversation_repo import ConversationRepository, MessageRepository
import uuid
import json
from app.services.ai_service import AIService
from app.graph.client import neo4j_dependency
from app.core.cache import redis_dependency
from redis.asyncio import Redis
from neo4j import AsyncDriver
from app.prompts.system_prompt import METADATA_ASSISTANT_SYSTEM_PROMPT

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
    session: AsyncSession = Depends(get_db_session),
    driver: AsyncDriver = Depends(neo4j_dependency),
    redis: Redis | None = Depends(redis_dependency),
):
    if not payload.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")
    svc = AIService(session, neo4j_driver=driver, redis=redis)

    # Non-stream: simple echo for now (can be upgraded to sync LLM)
    if not payload.stream:
        return await svc.simple_echo(uuid.UUID(current_user.id), payload.query, payload.conversation_id)

    async def event_stream():
        # status start
        yield f"event: status\ndata: {json.dumps({'message': 'Thinking...', 'tool': 'llm', 'progress': 5})}\n\n"

        # Get tools dynamically from MCP server
        try:
            tools = await svc.get_mcp_tools_schema()
        except Exception as e:
            # Fallback to empty tools if MCP server is not available
            tools = []
            yield f"event: status\ndata: {json.dumps({'message': f'Warning: MCP tools unavailable ({str(e)})', 'tool': 'system', 'progress': 10})}\n\n"

        # Prepare messages with system prompt
        base_messages = [
            {
                "role": "system",
                "content": METADATA_ASSISTANT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": payload.query},
        ]

        try:
            summary, statuses, actions, duration_ms = await svc.run_llm_with_tools(base_messages, tools, stream=False)
            for st in statuses:
                yield f"event: status\ndata: {json.dumps(st)}\n\n"
            if summary:
                yield f"event: data\ndata: {json.dumps({'type': 'text', 'content': summary})}\n\n"
            if actions:
                yield f"event: data\ndata: {json.dumps({'type': 'actions', 'content': actions})}\n\n"
            else:
                yield f"event: data\ndata: {json.dumps({'type': 'text', 'content': 'AI assistant暂未返回结果，请稍后重试'})}\n\n"
        except Exception as exc:
            err = {'type': 'text', 'content': 'AI assistant failed: ' + str(exc)}
            yield f"event: data\ndata: {json.dumps(err)}\n\n"
        yield f"event: status\ndata: {json.dumps({'message': 'Done', 'tool': 'llm', 'progress': 100})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: AsyncSession = Depends(get_db_session),
):
    repo = ConversationRepository(session)
    rows = await repo.list(user_id=uuid.UUID(current_user.id))
    return [ConversationListItem(id=str(r.id), title=r.title or "", created_at=r.created_at.isoformat(), updated_at=r.updated_at.isoformat()) for r in rows]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: AsyncSession = Depends(get_db_session),
):
    conv_repo = ConversationRepository(session)
    msg_repo = MessageRepository(session)
    conv = await conv_repo.get(uuid.UUID(conversation_id), uuid.UUID(current_user.id))
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = await msg_repo.list(uuid.UUID(conversation_id), uuid.UUID(current_user.id))
    return ConversationDetail(
        id=str(conv.id),
        title=conv.title or "",
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=[
            ConversationMessage(
                id=str(m.id),
                role=m.role,
                type=m.type,
                content=m.content,
                metadata=m.metadata or {},
                created_at=m.created_at.isoformat(),
            )
            for m in msgs
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    session: AsyncSession = Depends(get_db_session),
):
    conv_repo = ConversationRepository(session)
    ok = await conv_repo.soft_delete(uuid.UUID(conversation_id), uuid.UUID(current_user.id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
