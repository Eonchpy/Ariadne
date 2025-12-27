from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api import deps
from app.schemas.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.schemas.conversation import ConversationCreate, ConversationListItem, ConversationDetail, ConversationMessage
from app.core.llm_client import LLMClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db_session
from app.repositories.conversation_repo import ConversationRepository, MessageRepository
import uuid
import json
import asyncio
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    current_user: Annotated[User, Depends(deps.get_current_user)] = None,
    session: AsyncSession = Depends(get_db_session),
):
    if not payload.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")
    svc = AIService(session)
    # For now: non-stream structured echo; if stream=True, use SSE
    if not payload.stream:
        return await svc.simple_echo(uuid.UUID(current_user.id), payload.query, payload.conversation_id)

    async def event_stream():
        async for chunk in svc.sse_placeholder(payload.query):
            yield chunk

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
