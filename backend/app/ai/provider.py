"""Abstract AI provider interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Type

from pydantic import BaseModel


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


class AIProvider:
    """Pluggable AI provider. Implementations must return validated Pydantic models."""

    name: str = "base"

    async def complete(
        self,
        messages: List[ChatMessage],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        """Call the LLM and parse its output into the given Pydantic model."""
        raise NotImplementedError

    async def embed(self, text: str) -> List[float]:
        """Optional embedding helper (defaults to no-op)."""
        return []

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
    ) -> str:
        """Plain-text chat completion (used by copilot fallback)."""
        raise NotImplementedError
