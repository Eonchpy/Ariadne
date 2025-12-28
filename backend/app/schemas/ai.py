from __future__ import annotations

from typing import Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class AIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    type: Literal["text", "table", "action_card", "suggestions"] = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: Optional[str] = None
    message: Optional[str] = Field(default=None, exclude=True)
    stream: bool = True

    @model_validator(mode="after")
    def fill_query_from_message(self):
        if not self.query and self.message:
            self.query = self.message
        return self


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
