from __future__ import annotations

from typing import Any, List, Optional
import asyncio

from openai import AsyncOpenAI, OpenAI

from app.config import settings


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        async_mode: bool = True,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.api_base = api_base or settings.LLM_API_BASE
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        if async_mode:
            self.client = AsyncOpenAI(base_url=self.api_base, api_key=self.api_key, timeout=self.timeout)
        else:
            self.client = OpenAI(base_url=self.api_base, api_key=self.api_key, timeout=self.timeout)
        self.async_mode = async_mode

    async def achat(
        self,
        messages: List[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs,
    ):
        if not self.async_mode:
            raise RuntimeError("Client initialized without async support")
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": self.temperature,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        if tools:
            payload["tools"] = tools
        payload.update(kwargs)
        return await self.client.chat.completions.create(**payload)

    def chat(
        self,
        messages: List[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs,
    ):
        if self.async_mode:
            raise RuntimeError("Client is async; use achat")
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": self.temperature,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        if tools:
            payload["tools"] = tools
        payload.update(kwargs)
        return self.client.chat.completions.create(**payload)

