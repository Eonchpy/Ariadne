from __future__ import annotations

from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class AIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    type: Literal["text", "table", "action_card", "suggestions"] = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str
    stream: bool = False


class AIChatResponse(BaseModel):
    messages: list[AIMessage] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)


class AIConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class AIConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[AIMessage] = Field(default_factory=list)
