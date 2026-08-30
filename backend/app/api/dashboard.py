"""Dashboard summary endpoint."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AuditLog,
    EvaluationStatus,
    ProcurementProject,
    ProjectStatus,
    ProjectVendor,
    Proposal,
    ProposalStatus,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
    VendorScore,
    Vendor,
)
from app.models.user import User
from app.security import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def dashboard_summary(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    active_projects = (await db.execute(
        select(func.count(ProcurementProject.id)).where(
            ProcurementProject.status.in_([ProjectStatus.ACTIVE, ProjectStatus.EVALUATION, ProjectStatus.DRAFT])
        )
    )).scalar() or 0
    vendors_total = (await db.execute(select(func.count(Vendor.id)))).scalar() or 0
    proposals_total = (await db.execute(select(func.count(Proposal.id)))).scalar() or 0
    proposals_analyzed = (await db.execute(
        select(func.count(Proposal.id)).where(Proposal.status == ProposalStatus.COMPLETED)
    )).scalar() or 0
    pending_reviews = (await db.execute(
        select(func.count(Proposal.id)).where(
            Proposal.status.in_([ProposalStatus.UPLOADED, ProposalStatus.QUEUED, ProposalStatus.PROCESSING, ProposalStatus.EXTRACTING, ProposalStatus.ANALYZING, ProposalStatus.SCORING])
        )
    )).scalar() or 0

    high_risk = (await db.execute(
        select(func.count(Risk.id)).where(Risk.severity.in_([RiskSeverity.HIGH, RiskSeverity.CRITICAL]))
    )).scalar() or 0

    # Potential savings: difference between max and min year1 totals among eligible proposals
    all_scores = (await db.execute(
        select(VendorScore).where(VendorScore.is_eligible == True)  # noqa: E712
    )).scalars().all()
    prop_ids = [s.proposal_id for s in all_scores]
    if prop_ids:
        prices_res = await db.execute(
            select(Proposal)
            .options(selectinload(Proposal.pricing))
            .where(Proposal.id.in_(prop_ids))
        )
        prices = prices_res.scalars().all()
    else:
        prices = []

    y1_values = [float(p.pricing.year1_total) for p in prices if p.pricing and p.pricing.year1_total is not None]
    potential_savings = (max(y1_values) - min(y1_values)) if len(y1_values) >= 2 else 0.0

    # Vendor scores (for chart)
    score_rows = (await db.execute(
        select(Proposal, VendorScore, Vendor)
        .join(VendorScore, VendorScore.proposal_id == Proposal.id)
        .join(ProjectVendor, ProjectVendor.id == Proposal.project_vendor_id)
        .join(Vendor, Vendor.id == ProjectVendor.vendor_id)
    )).all()
    vendor_scores = [
        {
            "vendor_id": str(v.id),
            "vendor_name": v.company_name,
            "score": s.total_score,
            "rank": s.rank,
        }
        for p, s, v in score_rows
    ]
    vendor_scores.sort(key=lambda x: -(x["score"] or 0))

    # Cost comparison
    cost_rows = []
    for p in prices:
        if p.pricing and (p.pricing.year1_total or p.pricing.year3_total or p.pricing.year5_total):
            cost_rows.append({
                "vendor_id": str(p.vendor_id),
                "year1": float(p.pricing.year1_total or 0),
                "year3": float(p.pricing.year3_total or 0),
                "year5": float(p.pricing.year5_total or 0),
            })

    # Risk distribution
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for r in (await db.execute(select(Risk))).scalars().all():
        risk_dist[r.severity.value] = risk_dist.get(r.severity.value, 0) + 1

    # Compliance per proposal
    compliance_rows = []
    props_with_vendors = (await db.execute(
        select(Proposal)
        .options(selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor))
    )).scalars().all()

    for p in props_with_vendors:
        evals_q = (await db.execute(
            select(RequirementEvaluation.status, func.count(RequirementEvaluation.id))
            .where(RequirementEvaluation.proposal_id == p.id)
            .group_by(RequirementEvaluation.status)
        )).all()
        total = sum(c for _, c in evals_q)
        meets = sum(c for s, c in evals_q if s in (EvaluationStatus.MEETS, EvaluationStatus.PARTIALLY_MEETS))
        compliance_rows.append({
            "vendor_id": str(p.vendor_id),
            "vendor_name": p.project_vendor.vendor.company_name if p.project_vendor and p.project_vendor.vendor else "Vendor",
            "compliance": (meets / total * 100) if total else 0,
        })

    return {
        "cards": {
            "active_projects": active_projects,
            "vendors_evaluated": vendors_total,
            "proposals_analyzed": proposals_analyzed,
            "potential_savings": potential_savings,
            "high_risk_vendors": high_risk,
            "pending_reviews": pending_reviews,
        },
        "vendor_scores": vendor_scores,
        "cost_comparison": cost_rows,
        "risk_distribution": risk_dist,
        "compliance": compliance_rows,
    }