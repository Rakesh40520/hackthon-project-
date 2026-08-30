"""OpenAI implementation of AIProvider using JSON mode + Pydantic validation."""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional, Type

from pydantic import BaseModel, ValidationError

from app.ai.provider import AIProvider, ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self):
        from openai import AsyncOpenAI

        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is required for OpenAI provider")
        self.client = AsyncOpenAI(api_key=settings.AI_API_KEY, timeout=settings.AI_TIMEOUT_SECONDS)
        self.model = settings.AI_MODEL or "gpt-4o-mini"

    async def complete(
        self,
        messages: List[ChatMessage],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        schema = response_model.model_json_schema()
        sys_msg = ChatMessage(
            role="system",
            content=(
                "You are a precise procurement analyst. Return ONLY valid JSON that matches the schema. "
                "If a value is not stated in the source, return null or 'UNKNOWN' rather than guessing. "
                "Do not fabricate. Always include evidence when extracting claims."
            ),
        )
        schema_msg = ChatMessage(
            role="system",
            content=f"JSON schema to follow:\n{json.dumps(schema, indent=2)}",
        )
        all_msgs = [sys_msg, schema_msg] + list(messages)
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in all_msgs],
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
            max_tokens=max_tokens or settings.AI_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            data: Any = json.loads(content)
            return response_model.model_validate(data)
        except (ValidationError, ValueError) as e:
            logger.warning("OpenAI JSON parse error: %s; content=%s", e, content[:500])
            # Try to coerce / fix common issues
            try:
                fixed = _best_effort_json(content)
                return response_model.model_validate(fixed)
            except Exception:
                # Fallback: empty instance
                return response_model.model_validate(_empty_for_schema(response_model))

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
    ) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature if temperature is not None else settings.AI_TEMPERATURE,
        )
        return resp.choices[0].message.content or ""


def _best_effort_json(text: str) -> Any:
    """Extract first JSON object/array from text."""
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    end = max(text.rfind("}"), text.rfind("]"))
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    return json.loads(text)


def _empty_for_schema(model: Type[BaseModel]) -> dict:
    """Build a dict with default values for the schema fields."""
    try:
        return model.model_construct().model_dump()
    except Exception:
        return {}
