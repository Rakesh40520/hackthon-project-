"""Ollama local-model provider."""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional, Type

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.provider import AIProvider, ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self):
        self.base = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.AI_MODEL or "llama3.1"

    async def _post_json(self, path: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            r = await client.post(f"{self.base}{path}", json=payload)
            r.raise_for_status()
            return r.json()

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
        msgs = [{"role": "system", "content": f"{sys_prompt}\nSchema: {json.dumps(schema)}"}]
        msgs += [{"role": m.role, "content": m.content} for m in messages]
        payload = {
            "model": self.model,
            "messages": msgs,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature if temperature is not None else settings.AI_TEMPERATURE,
                "num_predict": max_tokens or settings.AI_MAX_TOKENS,
            },
        }
        data = await self._post_json("/api/chat", payload)
        content = data.get("message", {}).get("content", "{}")
        try:
            return response_model.model_validate(json.loads(content))
        except (ValidationError, ValueError) as e:
            logger.warning("Ollama JSON parse error: %s", e)
            return response_model.model_construct()

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature if temperature is not None else settings.AI_TEMPERATURE},
        }
        data = await self._post_json("/api/chat", payload)
        return data.get("message", {}).get("content", "")
