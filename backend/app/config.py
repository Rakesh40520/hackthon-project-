"""Application configuration via environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Procurement Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])
    FRONTEND_URL: str = "http://localhost:5173"

    # Security
    SECRET_KEY: str = "change-me-in-production-this-must-be-very-long-and-random-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    BCRYPT_ROUNDS: int = 12

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://procurement:procurement@localhost:5432/procurement"
    DATABASE_URL_SYNC: str = "postgresql://procurement:procurement@localhost:5432/procurement"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = Field(default_factory=lambda: [".pdf", ".docx", ".xlsx", ".csv", ".txt"])

    # AI
    AI_PROVIDER: Literal["openai", "anthropic", "gemini", "ollama", "mock"] = "mock"
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str = ""
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 4096
    AI_TIMEOUT_SECONDS: int = 120
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    # Default Scoring Weights
    DEFAULT_WEIGHT_PRICE: float = 0.30
    DEFAULT_WEIGHT_TECHNICAL: float = 0.25
    DEFAULT_WEIGHT_SECURITY: float = 0.15
    DEFAULT_WEIGHT_SUPPORT: float = 0.10
    DEFAULT_WEIGHT_IMPLEMENTATION: float = 0.10
    DEFAULT_WEIGHT_CONTRACT: float = 0.10


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()


settings = get_settings()
