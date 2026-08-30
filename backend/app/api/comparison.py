"""Vendor comparison endpoint."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    EvaluationStatus,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
    VendorScore,
    Vendor,
)
from app.models.user import User
from app.schemas.copilot import ComparisonOut, ComparisonVendorRow
from app.schemas.analysis import PricingDetailOut, RecommendationOut, VendorScoreOut
from app.security import get_current_active_user

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.get("/{project_id}", response_model=ComparisonOut)
async def compare_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    proj_res = await db.execute(
        select(ProcurementProject)
        .options(selectinload(ProcurementProject.project_vendors).selectinload(ProjectVendor.vendor))
        .where(ProcurementProject.id == project_id)
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    weights = {
        "price": float(project.weight_price),
        "technical": float(project.weight_technical),
        "security": float(project.weight_security),
        "support": float(project.weight_support),
        "implementation": float(project.weight_implementation),
        "contract": float(project.weight_contract),
    }

    rows: List[ComparisonVendorRow] = []
    ranking: List[Dict[str, Any]] = []

    for pv in project.project_vendors:
        prop_res = await db.execute(
            select(Proposal)
            .options(
                selectinload(Proposal.pricing),
                selectinload(Proposal.score).selectinload(VendorScore.components),
                selectinload(Proposal.recommendation),
                selectinload(Proposal.risks),
            )
            .where(Proposal.project_vendor_id == pv.id)
            .order_by(Proposal.created_at.desc())
        )
        proposal = prop_res.scalars().first()

        evals_res = await db.execute(
            select(RequirementEvaluation)
            .where(RequirementEvaluation.proposal_id == proposal.id) if proposal else select(RequirementEvaluation).where(False)
        )
        evals = evals_res.scalars().all()
        compliance = 0.0
        mandatory_meets = 0
        total_mandatory = 0
        if evals:
            meets = sum(1 for e in evals if e.status in (EvaluationStatus.MEETS, EvaluationStatus.PARTIALLY_MEETS))
            compliance = (meets / len(evals)) * 100
            for e in evals:
                if e.requirement_id:  # type: ignore[attr-defined]
                    pass
            # Track mandatory count via the related requirement
            from app.models import Requirement
            req_ids = {e.requirement_id for e in evals}
            if req_ids:
                reqs = (await db.execute(select(Requirement).where(Requirement.id.in_(req_ids)))).scalars().all()
                mand = {r.id for r in reqs if r.mandatory}
                total_mandatory = len(mand)
                mandatory_meets = sum(
                    1 for e in evals
                    if e.requirement_id in mand and e.status in (EvaluationStatus.MEETS, EvaluationStatus.PARTIALLY_MEETS)
                )

        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for r in (proposal.risks if proposal else []):
            risk_counts[r.severity.value] = risk_counts.get(r.severity.value, 0) + 1

        score_out = VendorScoreOut.model_validate(proposal.score) if proposal and proposal.score else None
        rec_out = RecommendationOut.model_validate(proposal.recommendation) if proposal and proposal.recommendation else None
        price_out = PricingDetailOut.model_validate(proposal.pricing) if proposal and proposal.pricing else None

        row = ComparisonVendorRow(
            vendor_id=str(pv.vendor_id),
            vendor_name=pv.vendor.company_name if pv.vendor else "Unknown",
            proposal_id=str(proposal.id) if proposal else None,
            pricing=price_out,
            score=score_out,
            recommendation=rec_out,
            risk_counts=risk_counts,
            compliance_pct=round(compliance, 1),
            meets_mandatory=mandatory_meets,
            total_mandatory=total_mandatory,
        )
        rows.append(row)
        if proposal and proposal.score:
            ranking.append({
                "vendor_id": str(pv.vendor_id),
                "vendor_name": pv.vendor.company_name if pv.vendor else "Unknown",
                "score": proposal.score.total_score,
                "rank": proposal.score.rank,
                "eligible": proposal.score.is_eligible,
            })
    ranking.sort(key=lambda x: (not x["eligible"], -x["score"]))
    for i, r in enumerate(ranking, start=1):
        if r["eligible"] and r["score"] is not None:
            r["rank"] = i

    return ComparisonOut(
        project_id=str(project.id),
        project_name=project.name,
        vendors=rows,
        weights=weights,
        ranking=ranking,
    )
