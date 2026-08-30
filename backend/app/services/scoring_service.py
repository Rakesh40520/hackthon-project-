"""Deterministic, explainable vendor scoring engine."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ProcurementProject,
    Proposal,
    ScoringComponent,
    VendorScore,
)

logger = logging.getLogger(__name__)

from app.services.scoring_subs2 import _explain_component as _explain  # noqa: E402
from app.services.scoring_subs import (  # noqa: E402
    _score_price,
    _score_technical,
    _score_security,
)
from app.services.scoring_subs2 import (  # noqa: E402
    _score_support,
    _score_implementation,
    _score_contract,
    _check_mandatory_failures,
)


async def compute_vendor_score(db: AsyncSession, proposal: Proposal, project: ProcurementProject) -> VendorScore:
    weights = {
        "price": float(project.weight_price),
        "technical": float(project.weight_technical),
        "security": float(project.weight_security),
        "support": float(project.weight_support),
        "implementation": float(project.weight_implementation),
        "contract": float(project.weight_contract),
    }
    total_w = sum(weights.values()) or 1.0
    weights = {k: v / total_w for k, v in weights.items()}

    price = await _score_price(db, proposal, project)
    technical = await _score_technical(db, proposal)
    security = await _score_security(db, proposal)
    support = await _score_support(db, proposal)
    implementation = await _score_implementation(db, proposal)
    contract = await _score_contract(db, proposal)

    sub_scores = {
        "price": price, "technical": technical, "security": security,
        "support": support, "implementation": implementation, "contract": contract,
    }
    total = sum(sub_scores[k] * weights[k] for k in sub_scores)

    inelig = await _check_mandatory_failures(db, proposal)
    is_eligible = len(inelig) == 0

    score_res = await db.execute(
        select(VendorScore)
        .options(selectinload(VendorScore.components))
        .where(VendorScore.proposal_id == proposal.id)
    )
    score = score_res.scalars().first()
    if score is None:
        score = VendorScore(
            proposal_id=proposal.id,
            total_score=round(total, 2),
            price_score=round(price, 2),
            technical_score=round(technical, 2),
            security_score=round(security, 2),
            support_score=round(support, 2),
            implementation_score=round(implementation, 2),
            contract_score=round(contract, 2),
            is_eligible=is_eligible,
            ineligibility_reasons=inelig,
            notes="Objective weighted score across 6 dimensions; LLM is not used for numeric scoring.",
        )
        db.add(score)
        await db.flush()
    else:
        score.total_score = round(total, 2)
        score.price_score = round(price, 2)
        score.technical_score = round(technical, 2)
        score.security_score = round(security, 2)
        score.support_score = round(support, 2)
        score.implementation_score = round(implementation, 2)
        score.contract_score = round(contract, 2)
        score.is_eligible = is_eligible
        score.ineligibility_reasons = inelig
        score.notes = "Objective weighted score across 6 dimensions; LLM is not used for numeric scoring."

    # Delete existing components
    comp_res = await db.execute(
        select(ScoringComponent).where(ScoringComponent.score_id == score.id)
    )
    for c in comp_res.scalars().all():
        await db.delete(c)
    await db.flush()

    for name, raw in sub_scores.items():
        comp = ScoringComponent(
            score_id=score.id, name=name, weight=weights[name],
            raw_score=round(raw, 2),
            weighted_score=round(raw * weights[name], 2),
            explanation=_explain(name),
        )
        db.add(comp)
    await db.commit()
    await db.refresh(score)
    return score


async def assign_ranks(db: AsyncSession, project_id: str) -> None:
    props_res = await db.execute(
        select(Proposal)
        .options(selectinload(Proposal.score))
        .where(Proposal.project_id == project_id)
    )
    proposals = props_res.scalars().all()
    eligible = [p for p in proposals if p.score and p.score.is_eligible]
    eligible.sort(key=lambda p: p.score.total_score, reverse=True)
    for i, p in enumerate(eligible, start=1):
        p.score.rank = i
    for p in proposals:
        if p.score and not p.score.is_eligible and p.score.rank is None:
            p.score.rank = None
    await db.commit()