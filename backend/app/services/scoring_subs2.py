"""Sub-score implementations (part 2): support, implementation, contract, mandatory check."""
from __future__ import annotations

import re
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    EvaluationStatus,
    Proposal,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
)


async def _score_support(db: AsyncSession, proposal: Proposal) -> float:
    text = (proposal.extracted_text or "").lower()
    if not text:
        return 50.0
    score = 50.0
    if "24/7" in text or "24 x 7" in text or "24x7" in text:
        score += 25
    if "dedicated account manager" in text or "customer success" in text:
        score += 10
    if "training" in text:
        score += 10
    if "support" in text:
        score += 5
    return min(100.0, score)


async def _score_implementation(db: AsyncSession, proposal: Proposal) -> float:
    text = (proposal.extracted_text or "").lower()
    if not text:
        return 50.0
    score = 60.0
    mm = re.search(r"(\d{1,3})\s*(?:days?|d)\b", text)
    if mm:
        try:
            days = int(mm.group(1))
            if days <= 30:
                score += 35
            elif days <= 60:
                score += 25
            elif days <= 90:
                score += 15
            elif days <= 180:
                score += 5
            else:
                score -= 10
        except ValueError:
            pass
    if "phased" in text or "rollout plan" in text:
        score += 5
    return max(0.0, min(100.0, score))


async def _score_contract(db: AsyncSession, proposal: Proposal) -> float:
    res = await db.execute(select(Risk).where(Risk.proposal_id == proposal.id))
    risks = res.scalars().all()
    score = 100.0
    for r in risks:
        if r.severity == RiskSeverity.CRITICAL:
            score -= 30
        elif r.severity == RiskSeverity.HIGH:
            score -= 18
        elif r.severity == RiskSeverity.MEDIUM:
            score -= 8
        else:
            score -= 3
    return max(0.0, min(100.0, score))


async def _check_mandatory_failures(db: AsyncSession, proposal: Proposal) -> List[str]:
    res = await db.execute(
        select(RequirementEvaluation)
        .options(selectinload(RequirementEvaluation.requirement))
        .where(RequirementEvaluation.proposal_id == proposal.id)
    )
    evals = res.scalars().all()
    failed: List[str] = []
    for e in evals:
        if e.requirement.mandatory and e.status in (EvaluationStatus.DOES_NOT_MEET, EvaluationStatus.UNKNOWN):
            failed.append(
                f"Mandatory requirement not met: {e.requirement.name} (status={e.status.value})"
            )
    return failed


def _explain_component(name: str) -> str:
    explainers = {
        "price": "Lower total cost gives a higher price score; missing pricing defaults to 40.",
        "technical": "Average of requirement evaluations, weighted by requirement weight.",
        "security": "Based on explicit encryption/SSO/SAML/OAuth claims from the proposal.",
        "support": "Boosted by 24/7 support, dedicated account manager, training references.",
        "implementation": "Boosted by shorter implementation timeframes and rollout plans.",
        "contract": "Reduced by detected risks (severity-weighted deductions).",
    }
    return explainers.get(name, "")
