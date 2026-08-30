"""AI provider factory."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.ai.mock_provider import MockProvider
from app.ai.provider import AIProvider
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """Return a configured AI provider singleton."""
    provider_name = settings.AI_PROVIDER.lower()
    try:
        if provider_name == "openai":
            from app.ai.openai_provider import OpenAIProvider
            return OpenAIProvider()
        if provider_name == "anthropic":
            from app.ai.anthropic_provider import AnthropicProvider
            return AnthropicProvider()
        if provider_name == "gemini":
            from app.ai.gemini_provider import GeminiProvider
            return GeminiProvider()
        if provider_name == "ollama":
            from app.ai.ollama_provider import OllamaProvider
            return OllamaProvider()
        if provider_name == "mock":
            return MockProvider()
    except Exception as e:  # pragma: no cover
        logger.warning("Failed to initialize AI provider '%s': %s — falling back to mock", provider_name, e)
        return MockProvider()
    logger.info("Unknown AI provider '%s' — using mock", provider_name)
    return MockProvider()
