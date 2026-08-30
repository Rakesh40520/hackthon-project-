"""Anthropic Claude implementation."""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional, Type

from pydantic import BaseModel, ValidationError

from app.ai.provider import AIProvider, ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self):
        from anthropic import AsyncAnthropic

        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is required for Anthropic provider")
        self.client = AsyncAnthropic(api_key=settings.AI_API_KEY, timeout=settings.AI_TIMEOUT_SECONDS)
        self.model = settings.AI_MODEL or "claude-3-5-sonnet-20241022"

    async def complete(
        self,
        messages: List[ChatMessage],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        schema = response_model.model_json_schema()
        sys_prompt = (
            "You are a precise procurement analyst. Return ONLY valid JSON matching the schema. "
            "Never fabricate. Use null or 'UNKNOWN' for missing data. Always include evidence."
        )
        user_payload = (
            f"JSON SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
            f"USER MESSAGES:\n"
            + "\n\n---\n\n".join(f"[{m.role}]\n{m.content}" for m in messages)
        )
        resp = await self.client.messages.create(
            model=self.model,
            system=sys_prompt,
            max_tokens=max_tokens or settings.AI_MAX_TOKENS,
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
            messages=[{"role": "user", "content": user_payload}],
        )
        content = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                content += block.text
        try:
            data: Any = json.loads(content)
            return response_model.model_validate(data)
        except (ValidationError, ValueError) as e:
            logger.warning("Anthropic JSON parse error: %s", e)
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return response_model.model_validate(json.loads(content[start : end + 1]))
                except Exception:
                    pass
            return response_model.model_construct()

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
    ) -> str:
        sys_content = next((m.content for m in messages if m.role == "system"), "You are a helpful procurement assistant.")
        user_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        if not user_msgs:
            user_msgs = [{"role": "user", "content": "Hello"}]
        resp = await self.client.messages.create(
            model=self.model,
            system=sys_content,
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
            messages=user_msgs,
        )
        text = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text += block.text
        return text
