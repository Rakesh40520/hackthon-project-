"""Celery worker configuration and tasks."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from celery import Celery

from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

celery_app = Celery(
    "procurement",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.celery_app"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,
    task_soft_time_limit=540,
    broker_connection_retry_on_startup=True,
)


def run_analysis_task(proposal_id: str) -> dict[str, Any]:
    """Synchronous entrypoint that runs the async analysis pipeline."""
    from app.services.analysis_orchestrator import run_full_analysis

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            await run_full_analysis(db, proposal_id)

    asyncio.run(_run())
    return {"proposal_id": proposal_id, "status": "completed"}


@celery_app.task(name="procurement.run_analysis", bind=True, max_retries=2)
def celery_run_analysis(self, proposal_id: str) -> dict[str, Any]:
    try:
        return run_analysis_task(proposal_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("Celery analysis task failed")
        raise self.retry(exc=exc, countdown=10)
