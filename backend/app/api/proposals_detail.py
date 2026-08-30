"""Proposal detail endpoint."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AnalysisJob,
    ClarificationQuestion,
    ProjectVendor,
    Proposal,
    RequirementEvaluation,
    VendorScore,
)
from app.models.user import User
from app.schemas.proposal import (
    AnalysisJobOut,
    ClarificationQuestionOut,
    ExtractedFieldOut,
    MissingInformationOut,
    PricingDetailOut,
    ProposalDetailOut,
    ProposalDocumentOut,
    ProposalOut,
    RequirementEvaluationOut,
    RiskOut,
    VendorScoreOut,
    RecommendationOut,
)
from app.security import get_current_active_user

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.get("/{proposal_id}", response_model=ProposalDetailOut)
async def get_proposal_detail(
    proposal_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Proposal)
        .options(
            selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor),
            selectinload(Proposal.documents),
            selectinload(Proposal.pricing),
            selectinload(Proposal.extracted_fields),
            selectinload(Proposal.risks),
            selectinload(Proposal.missing_info),
            selectinload(Proposal.score).selectinload(VendorScore.components),
            selectinload(Proposal.recommendation),
        )
        .where(Proposal.id == proposal_id)
    )
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Proposal not found")

    evals_res = await db.execute(
        select(RequirementEvaluation)
        .options(selectinload(RequirementEvaluation.requirement))
        .where(RequirementEvaluation.proposal_id == p.id)
    )
    evals = evals_res.scalars().all()

    clars_res = await db.execute(
        select(ClarificationQuestion).where(ClarificationQuestion.proposal_id == p.id)
    )
    clars = clars_res.scalars().all()

    job_res = await db.execute(
        select(AnalysisJob).where(AnalysisJob.proposal_id == p.id).order_by(desc(AnalysisJob.created_at))
    )
    job = job_res.scalars().first()

    docs = [ProposalDocumentOut.model_validate(d).model_dump() for d in p.documents]
    eval_out = []
    for e in evals:
        data = RequirementEvaluationOut.model_validate(e).model_dump()
        data["requirement_name"] = e.requirement.name if e.requirement else None
        eval_out.append(data)

    base = ProposalOut.model_validate(p).model_dump()
    if p.project_vendor and p.project_vendor.vendor:
        base["vendor_name"] = p.project_vendor.vendor.company_name
        base["vendor_company"] = p.project_vendor.vendor.company_name

    # Remove keys that ProposalDetailOut will receive as explicit keyword args
    # (ProposalOut has score/rank as flat floats; ProposalDetailOut has them as nested objects)
    for key in (
        "score", "rank", "documents", "pricing", "extracted_fields",
        "evaluations", "risks", "missing_info", "clarification_questions",
        "recommendation", "current_job",
    ):
        base.pop(key, None)

    return ProposalDetailOut(
        **base,
        documents=docs,
        pricing=PricingDetailOut.model_validate(p.pricing) if p.pricing else None,
        extracted_fields=[ExtractedFieldOut.model_validate(f) for f in p.extracted_fields],
        evaluations=eval_out,
        risks=[RiskOut.model_validate(r) for r in p.risks],
        missing_info=[MissingInformationOut.model_validate(m) for m in p.missing_info],
        clarification_questions=[ClarificationQuestionOut.model_validate(c) for c in clars],
        score=VendorScoreOut.model_validate(p.score) if p.score else None,
        recommendation=RecommendationOut.model_validate(p.recommendation) if p.recommendation else None,
        current_job=AnalysisJobOut.model_validate(job) if job else None,
    )
