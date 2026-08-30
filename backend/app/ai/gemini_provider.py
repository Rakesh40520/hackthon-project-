"""Google Gemini implementation."""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional, Type

from pydantic import BaseModel, ValidationError

from app.ai.provider import AIProvider, ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self):
        import google.generativeai as genai

        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is required for Gemini provider")
        genai.configure(api_key=settings.AI_API_KEY)
        self.model_name = settings.AI_MODEL or "gemini-1.5-flash"
        self._configure = genai.GenerationConfig(
            temperature=settings.AI_TEMPERATURE,
            max_output_tokens=settings.AI_MAX_TOKENS,
            response_mime_type="application/json",
        )
        self._genai = genai

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
        user_text = (
            f"SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
            f"MESSAGES:\n" + "\n\n---\n\n".join(f"[{m.role}] {m.content}" for m in messages)
        )
        model = self._genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=sys_prompt,
            generation_config=self._configure,
        )
        resp = await model.generate_content_async(user_text)
        content = resp.text or "{}"
        try:
            return response_model.model_validate(json.loads(content))
        except (ValidationError, ValueError) as e:
            logger.warning("Gemini JSON parse error: %s", e)
            return response_model.model_construct()

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
    ) -> str:
        model = self._genai.GenerativeModel(model_name=self.model_name)
        history = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            history.append({"role": role, "parts": [m.content]})
        chat = model.start_chat(history=history[:-1] if history else [])
        last = messages[-1].content if messages else "Hello"
        resp = await chat.send_message_async(last)
        return resp.text or ""
