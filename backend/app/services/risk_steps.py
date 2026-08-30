"""Risk detection and missing information steps."""
from __future__ import annotations

import json
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import MissingInfoList, RiskList, get_ai_provider
from app.ai.provider import ChatMessage
from app.models import MissingInformation, Proposal, Risk, RiskCategory, RiskSeverity
from app.services.extraction_service import _chunk_text

logger = logging.getLogger(__name__)


async def analyze_risks(db: AsyncSession, proposal: Proposal, text: str) -> List[Risk]:
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Analyze this proposal for commercial, technical, security, contract, support and "
            "compliance risks. Return a JSON list `risks` with category, severity, title, description, "
            "evidence_quote, evidence_document, evidence_page, recommendation. Only flag real risks. "
            "If none, return an empty list.\n\n" + _chunk_text(text)
        ))
    ]
    res: RiskList = await ai.complete(messages=msgs, response_model=RiskList)
    risks: List[Risk] = []
    for it in res.risks:
        try:
            cat = RiskCategory(it.category)
        except ValueError:
            cat = RiskCategory.COMMERCIAL
        try:
            sev = RiskSeverity(it.severity)
        except ValueError:
            sev = RiskSeverity.MEDIUM
        r = Risk(
            proposal_id=proposal.id, category=cat, severity=sev, title=it.title,
            description=it.description, evidence_quote=it.evidence_quote,
            evidence_document=it.evidence_document, evidence_page=it.evidence_page,
            recommendation=it.recommendation,
        )
        db.add(r)
        risks.append(r)
    await db.commit()
    return risks


async def detect_missing(db: AsyncSession, proposal: Proposal, text: str) -> List[MissingInformation]:
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Identify critical missing information in this proposal (data residency, RTO/RPO, "
            "SLA credits, escalation, API limits, implementation timeline, etc). Return JSON list "
            "`items` with field_name, importance, why_it_matters. Only return items genuinely missing.\n\n"
            + _chunk_text(text)
        ))
    ]
    res: MissingInfoList = await ai.complete(messages=msgs, response_model=MissingInfoList)
    items: List[MissingInformation] = []
    for it in res.items:
        m = MissingInformation(
            proposal_id=proposal.id, field_name=it.field_name,
            importance=it.importance, why_it_matters=it.why_it_matters,
        )
        db.add(m)
        items.append(m)
    await db.commit()
    return items


async def generate_clarifications(db: AsyncSession, proposal: Proposal) -> List:
    from app.ai import ClarificationQuestionsResult
    from app.models import ClarificationQuestion

    ai = get_ai_provider()
    miss_res = await db.execute(select(MissingInformation).where(MissingInformation.proposal_id == proposal.id))
    missing = [m.field_name for m in miss_res.scalars().all()]
    msgs = [
        ChatMessage(role="user", content=(
            "Generate clarification questions for the vendor about the following missing fields. "
            "Each question should be specific, professional, and 1-2 sentences.\n\n"
            f"MISSING_FIELDS: {json.dumps(missing)}"
        ))
    ]
    res: ClarificationQuestionsResult = await ai.complete(messages=msgs, response_model=ClarificationQuestionsResult)
    out = []
    old = await db.execute(select(ClarificationQuestion).where(ClarificationQuestion.proposal_id == proposal.id))
    for o in old.scalars().all():
        await db.delete(o)
    await db.flush()
    for q in res.questions:
        c = ClarificationQuestion(proposal_id=proposal.id, question=q, priority="MEDIUM", category="general")
        db.add(c)
        out.append(c)
    await db.commit()
    return out
