from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.ai import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, user_id: uuid.UUID, limit: int = 50) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.is_deleted == False)  # noqa: E712
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, conv_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id, Conversation.is_deleted == False  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, title: str) -> Conversation:
        conv = Conversation(user_id=user_id, title=title or "")
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def soft_delete(self, conv_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = (
            update(Conversation)
            .where(Conversation.id == conv_id, Conversation.user_id == user_id, Conversation.is_deleted == False)  # noqa: E712
            .values(is_deleted=True)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, conv_id: uuid.UUID, role: str, type_: str, content: str, metadata: dict) -> Message:
        msg = Message(conversation_id=conv_id, role=role, type=type_, content=content, meta=metadata or {})
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def list(self, conv_id: uuid.UUID, user_id: uuid.UUID) -> List[Message]:
        stmt = (
            select(Message)
            .join(Conversation)
            .where(
                Message.conversation_id == conv_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,  # noqa: E712
            )
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
