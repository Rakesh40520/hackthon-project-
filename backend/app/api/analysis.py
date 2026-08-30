"""Analysis run endpoint."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AnalysisJob, AuditAction, Proposal
from app.models.user import User
from app.schemas.common import MessageResponse
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/run/{proposal_id}", response_model=MessageResponse)
async def run_analysis(
    proposal_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    from app.api.proposals import _safe_run
    background_tasks.add_task(_safe_run, str(p.id))
    await record_audit(db, user, AuditAction.ANALYSIS_START, "proposal", p.id)
    await db.commit()
    return MessageResponse(message="Analysis queued", success=True)


@router.post("/rescore/{project_id}", response_model=MessageResponse)
async def rescore_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.analysis_orchestrator import run_full_analysis
    from app.services.scoring_service import assign_ranks
    from app.models import ProcurementProject, ProjectVendor, VendorScore
    from sqlalchemy.orm import selectinload

    res = await db.execute(
        select(ProcurementProject)
        .options(selectinload(ProcurementProject.project_vendors).selectinload(ProjectVendor.proposals))
        .where(ProcurementProject.id == project_id)
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for pv in project.project_vendors:
        for p in pv.proposals:
            try:
                await run_full_analysis(db, str(p.id))
            except Exception:
                # ignore failures during rescore; partial results stay
                pass
    await assign_ranks(db, str(project_id))
    await record_audit(db, user, AuditAction.SCORE_COMPUTED, "project", project_id, description="Rescored all proposals")
    await db.commit()
    return MessageResponse(message="Rescore complete", success=True)
