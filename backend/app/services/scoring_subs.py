"""Sub-score implementations for the scoring engine (part 1)."""
from __future__ import annotations

import re
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    EvaluationStatus,
    ExtractedField,
    PricingDetail,
    ProcurementProject,
    Proposal,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
)


async def _score_price(db: AsyncSession, proposal: Proposal, project: ProcurementProject) -> float:
    p_res = await db.execute(select(PricingDetail).where(PricingDetail.proposal_id == proposal.id))
    pricing = p_res.scalars().first()
    if not pricing or pricing.year1_total is None:
        return 75.0
    res = await db.execute(
        select(PricingDetail)
        .join(Proposal, PricingDetail.proposal_id == Proposal.id)
        .where(Proposal.project_id == project.id)
    )
    others = res.scalars().all()
    values = [float(p.year1_total) for p in others if p.year1_total is not None]
    if not values:
        return 75.0
    my_value = float(pricing.year1_total)
    cheapest = min(values)
    if cheapest <= 0:
        return 75.0
    ratio = cheapest / my_value
    if ratio >= 1.0:
        return 100.0
    if ratio >= 0.75:
        return 80.0 + (ratio - 0.75) * 80
    if ratio >= 0.5:
        return 60.0 + (ratio - 0.5) * 80
    if ratio >= 0.25:
        return 30.0 + (ratio - 0.25) * 120
    return max(5.0, ratio * 120)


async def _score_technical(db: AsyncSession, proposal: Proposal) -> float:
    res = await db.execute(
        select(RequirementEvaluation)
        .options(selectinload(RequirementEvaluation.requirement))
        .where(RequirementEvaluation.proposal_id == proposal.id)
    )
    evals = res.scalars().all()
    if evals:
        total_w, total_s = 0.0, 0.0
        for e in evals:
            w = float(e.requirement.weight or 1.0)
            total_w += w
            if e.status == EvaluationStatus.MEETS:
                total_s += 100 * w
            elif e.status == EvaluationStatus.PARTIALLY_MEETS:
                total_s += 60 * w
            elif e.status == EvaluationStatus.UNKNOWN:
                total_s += 30 * w
            else:
                total_s += 0 * w
        if total_w:
            return total_s / total_w
    tech_fields = await db.execute(
        select(ExtractedField).where(
            ExtractedField.proposal_id == proposal.id, ExtractedField.field_group == "technical"
        )
    )
    fields = tech_fields.scalars().all()
    if not fields:
        return 50.0
    true_count = sum(1 for f in fields if f.value and f.value.lower() in ("true", "yes", "1"))
    return min(100.0, (true_count / max(1, len(fields))) * 100 + 30)


async def _score_security(db: AsyncSession, proposal: Proposal) -> float:
    res = await db.execute(
        select(ExtractedField).where(
            ExtractedField.proposal_id == proposal.id, ExtractedField.field_group == "technical",
            ExtractedField.field_name.in_([
                "encryption_at_rest", "encryption_in_transit", "sso", "saml", "oauth",
            ]),
        )
    )
    fields = res.scalars().all()
    if not fields:
        return 45.0
    true_count = sum(1 for f in fields if f.value and f.value.lower() in ("true", "yes", "1"))
    return min(100.0, (true_count / max(1, len(fields))) * 100 + 20)