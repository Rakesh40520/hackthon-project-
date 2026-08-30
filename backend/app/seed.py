"""Seed demo data: admin user, project, vendors, requirements, sample proposals."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import settings
from app.database import Base
from app.seed_helpers import ensure_user, ensure_project, ensure_vendors
from app.seed_helpers2 import ensure_requirements, ensure_project_vendors, ensure_proposals

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    sample_dir = Path(__file__).resolve().parent.parent.parent / "sample_data" / "proposals"
    async with Session() as db:
        user = await ensure_user(db)
        project = await ensure_project(db, user)
        vendors = await ensure_vendors(db)
        await ensure_requirements(db, project)
        pvs = await ensure_project_vendors(db, project, vendors)
        await ensure_proposals(db, pvs, sample_dir)
    await engine.dispose()
    logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
