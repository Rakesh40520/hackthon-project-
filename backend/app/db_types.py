"""Cross-database compatible column types.

Uses PostgreSQL native types when running on Postgres, and falls back to
SQLite-compatible generic types otherwise. This lets the same models
work on both `postgresql+asyncpg://` and `sqlite+aiosqlite://` URLs,
which is very convenient for local development and tests.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CHAR, JSON, TypeDecorator
from sqlalchemy.types import TypeEngine


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID column.

    Stores UUIDs as native ``UUID`` on Postgres and as ``CHAR(36)`` on
    other dialects (SQLite). Always exposes Python ``uuid.UUID`` objects.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: TypeEngine) -> TypeEngine:
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: TypeEngine) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value: Any, dialect: TypeEngine) -> Any:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSONBCompat(TypeDecorator):
    """JSONB on Postgres, JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: TypeEngine) -> TypeEngine:
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
