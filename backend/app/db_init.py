"""Initialise database tables (development helper).

For production use Alembic migrations. This file creates all tables using
SQLAlchemy's metadata so a developer can `python -m app.db_init` immediately.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app import models  # noqa: F401  -- register models

logger = logging.getLogger(__name__)


async def _create() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    logger.info("Database schema created at %s", settings.DATABASE_URL.split("@")[-1])


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_create())


if __name__ == "__main__":
    main()
