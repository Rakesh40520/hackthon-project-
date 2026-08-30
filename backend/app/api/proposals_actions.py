"""Proposal actions: reanalyze, job status, delete, clarifications."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.proposals import _safe_run
from app.database import get_db
from app.models import (
    AnalysisJob,
    AuditAction,
    ClarificationQuestion,
    Proposal,
    ProposalDocument,
    ProposalStatus,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.analysis import AnalysisJobOut
from app.schemas.proposal import ClarificationQuestionOut
from app.security import get_current_active_user
from app.services.audit_service import record_audit
from app.utils.storage import get_storage

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("/{proposal_id}/reanalyze", response_model=MessageResponse)
async def reanalyze(
    proposal_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    p.status = ProposalStatus.QUEUED
    p.progress = 0
    p.error_message = None
    await db.commit()
    background_tasks.add_task(_safe_run, str(p.id))
    await record_audit(db, user, AuditAction.ANALYSIS_START, "proposal", p.id)
    await db.commit()
    return MessageResponse(message="Re-analysis queued", success=True)


@router.get("/{proposal_id}/job", response_model=Optional[AnalysisJobOut])
async def get_proposal_job(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AnalysisJob).where(AnalysisJob.proposal_id == proposal_id).order_by(desc(AnalysisJob.created_at))
    )
    job = res.scalars().first()
    return AnalysisJobOut.model_validate(job) if job else None


@router.delete("/{proposal_id}", response_model=MessageResponse)
async def delete_proposal(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    await record_audit(db, user, AuditAction.PROPOSAL_DELETE, "proposal", p.id, description=p.title)
    storage = get_storage()
    docs = (await db.execute(
        select(ProposalDocument).where(ProposalDocument.proposal_id == p.id)
    )).scalars().all()
    for d in docs:
        storage.delete(d.storage_path)
    await db.delete(p)
    await db.commit()
    return MessageResponse(message="Proposal deleted", success=True)


@router.post("/{proposal_id}/clarify", response_model=List[ClarificationQuestionOut])
async def regenerate_clarifications(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.risk_steps import generate_clarifications as _gen
    res = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    qs = await _gen(db, p)
    await record_audit(db, user, AuditAction.CLARIFICATION_GENERATED, "proposal", p.id)
    await db.commit()
    return [ClarificationQuestionOut.model_validate(q) for q in qs]
