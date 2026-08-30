"""Job lifecycle management for analysis tasks."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalysisJob, JobStage, JobStatus


async def get_or_create_job(db: AsyncSession, proposal_id: str) -> AnalysisJob:
    res = await db.execute(
        select(AnalysisJob).where(AnalysisJob.proposal_id == proposal_id).order_by(AnalysisJob.created_at.desc())
    )
    job = res.scalars().first()
    if job and job.status in (JobStatus.RUNNING, JobStatus.PENDING):
        return job
    job = AnalysisJob(proposal_id=proposal_id, status=JobStatus.PENDING, progress=0)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(
    db: AsyncSession,
    job: AnalysisJob,
    *,
    status: Optional[JobStatus] = None,
    stage: Optional[JobStage] = None,
    progress: Optional[int] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    if status is not None:
        job.status = status
    if stage is not None:
        job.current_stage = stage
    if progress is not None:
        job.progress = progress
    if message is not None:
        job.stage_message = message
    if error is not None:
        job.error_message = error
    if started and not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    if completed:
        job.completed_at = datetime.now(timezone.utc)
    await db.commit()
