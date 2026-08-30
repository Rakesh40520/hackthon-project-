"""Recommendation endpoints."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AuditAction,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    Recommendation,
    VendorScore,
)
from app.models.user import User
from app.schemas.analysis import RecommendationOut
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{project_id}", response_model=List[RecommendationOut])
async def list_recommendations(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    proj = (await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    res = await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.proposal))
        .join(Proposal, Proposal.id == Recommendation.proposal_id)
        .where(Proposal.project_id == project_id)
        .order_by(Recommendation.rank.asc().nullslast())
    )
    out: List[RecommendationOut] = []
    for r in res.scalars().all():
        o = RecommendationOut.model_validate(r)
        out.append(o)
    return out


@router.get("/{project_id}/top", response_model=RecommendationOut)
async def get_top_recommendation(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Recommendation)
        .options(selectinload(Recommendation.proposal))
        .join(Proposal, Proposal.id == Recommendation.proposal_id)
        .where(Proposal.project_id == project_id, Recommendation.recommended == True)  # noqa: E712
        .order_by(Recommendation.rank.asc().nullslast())
    )
    r = res.scalars().first()
    if not r:
        raise HTTPException(status_code=404, detail="No top recommendation yet")
    return RecommendationOut.model_validate(r)


@router.post("/regenerate/{proposal_id}", response_model=RecommendationOut)
async def regenerate_recommendation(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Proposal)
        .options(
            selectinload(Proposal.score).selectinload(VendorScore.components),
            selectinload(Proposal.recommendation),
        )
        .where(Proposal.id == proposal_id)
    )
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if not p.score:
        raise HTTPException(status_code=400, detail="Run analysis first")
    proj = (await db.execute(select(ProcurementProject).where(ProcurementProject.id == p.project_id))).scalar_one()
    from app.services.analysis_orchestrator import generate_recommendation
    rec = await generate_recommendation(db, p, proj, p.score)
    await record_audit(db, user, AuditAction.RECOMMENDATION_GENERATED, "proposal", p.id)
    await db.commit()
    return RecommendationOut.model_validate(rec)
