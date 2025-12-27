from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = None
    first_message: str | None = None


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationMessage(BaseModel):
    id: str
    role: str
    type: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ConversationMessage] = Field(default_factory=list)
