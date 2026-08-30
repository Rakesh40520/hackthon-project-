"""Requirement evaluation, risk detection, missing info, clarifications."""
from __future__ import annotations

import json
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import (
    ClarificationQuestionsResult,
    MissingInfoList,
    RequirementEvaluationList,
    RiskList,
    get_ai_provider,
)
from app.ai.provider import ChatMessage
from app.models import (
    ClarificationQuestion,
    EvaluationStatus,
    MissingInformation,
    ProcurementProject,
    Proposal,
    Requirement,
    RequirementEvaluation,
    Risk,
    RiskCategory,
    RiskSeverity,
)
from app.services.extraction_service import _chunk_text

logger = logging.getLogger(__name__)


async def evaluate_requirements(
    db: AsyncSession, proposal: Proposal, project: ProcurementProject, text: str,
) -> List[RequirementEvaluation]:
    ai = get_ai_provider()
    reqs_res = await db.execute(
        select(Requirement).where(Requirement.project_id == project.id).order_by(Requirement.order_index)
    )
    reqs = reqs_res.scalars().all()
    if not reqs:
        return []

    req_payload = []
    for r in reqs:
        kw = [r.name]
        if r.description:
            kw.extend([w for w in r.description.split() if len(w) > 3][:5])
        if r.expected_value:
            kw.append(r.expected_value)
        req_payload.append({
            "id": str(r.id), "name": r.name, "description": r.description,
            "keywords": kw, "mandatory": r.mandatory, "priority": r.priority.value,
        })

    msgs = [
        ChatMessage(role="user", content=(
            "Evaluate each requirement against the proposal. Return a list `evaluations` where each "
            "item has requirement_name, status (MEETS|PARTIALLY_MEETS|DOES_NOT_MEET|UNKNOWN), "
            "score (0-100), reason, confidence (0-1), evaluated_value and evidence (document, page, section, quote). "
            "Do not fabricate. Use UNKNOWN if no information is present.\n\n"
            f"REQUIREMENTS_JSON: {json.dumps(req_payload)}\n\n" + _chunk_text(text)
        ))
    ]
    res: RequirementEvaluationList = await ai.complete(messages=msgs, response_model=RequirementEvaluationList)
    by_name = {ev.requirement_name.lower(): ev for ev in res.evaluations}

    evaluations: List[RequirementEvaluation] = []
    for r in reqs:
        ev = by_name.get(r.name.lower())
        if not ev:
            ev_obj = RequirementEvaluation(
                proposal_id=proposal.id, requirement_id=r.id,
                status=EvaluationStatus.UNKNOWN, score=0.0,
                reason="No information found", confidence=0.0,
            )
        else:
            try:
                status_enum = EvaluationStatus(ev.status)
            except ValueError:
                status_enum = EvaluationStatus.UNKNOWN
            ev_obj = RequirementEvaluation(
                proposal_id=proposal.id, requirement_id=r.id,
                status=status_enum, score=float(ev.score),
                reason=ev.reason, confidence=float(ev.confidence),
                evidence_document=ev.evidence.document,
                evidence_page=ev.evidence.page,
                evidence_section=ev.evidence.section,
                evidence_quote=ev.evidence.quote,
                evaluated_value=ev.evaluated_value,
            )
        db.add(ev_obj)
        evaluations.append(ev_obj)
    await db.commit()
    return evaluations
