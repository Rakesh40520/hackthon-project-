"""AI Procurement Copilot endpoint."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import CopilotAnswer, get_ai_provider
from app.ai.provider import ChatMessage
from app.config import settings
from app.database import get_db
from app.models import (
    EvaluationStatus,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    Recommendation,
    Requirement,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
    VendorScore,
)
from app.models.user import User
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotCitation,
)
from app.security import get_current_active_user

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
async def copilot_chat(payload: CopilotChatRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    proj = (await db.execute(select(ProcurementProject).where(ProcurementProject.id == payload.project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build context from proposals in the project
    prop_res = await db.execute(
        select(Proposal)
        .options(
            selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor),
            selectinload(Proposal.score),
            selectinload(Proposal.recommendation),
            selectinload(Proposal.risks),
        )
        .where(Proposal.project_id == payload.project_id)
    )
    proposals = prop_res.scalars().all()
    if payload.vendor_id:
        proposals = [p for p in proposals if str(p.vendor_id) == payload.vendor_id]

    # Build a concise structured context
    ctx_lines = [f"Project: {proj.name}", f"Budget: {proj.budget or 'n/a'} {proj.currency or ''}"]
    for p in proposals:
        name = p.project_vendor.vendor.company_name if p.project_vendor and p.project_vendor.vendor else "Vendor"
        score = f"{p.score.total_score:.1f}" if p.score else "n/a"
        elig = "eligible" if (p.score and p.score.is_eligible) else "ineligible"
        rec = p.recommendation.decision if p.recommendation else "n/a"
        high = [r.title for r in p.risks if r.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL)]
        ctx_lines.append(
            f"\nVendor: {name}\n  Score: {score} ({elig})\n  Decision: {rec}\n  High risks: {', '.join(high) or 'none'}\n"
            f"  Excerpt: {(p.extracted_text or '')[:600]}"
        )

    sys = (
        "You are a procurement copilot. Answer using ONLY the provided project context. "
        "If the information is not in the context, say: 'I couldn't find this information in the submitted proposals.' "
        "Cite documents with [Document: name, Page: N] when you reference text."
    )
    msgs = [ChatMessage(role="system", content=sys)]
    msgs.extend([ChatMessage(role=m.role, content=m.content) for m in payload.messages])
    msgs.append(ChatMessage(role="user", content="PROJECT CONTEXT:\n" + "\n".join(ctx_lines)))

    ai = get_ai_provider()
    try:
        result: CopilotAnswer = await ai.complete(messages=msgs, response_model=CopilotAnswer)
    except Exception:
        # Fall back to plain chat
        text = await ai.chat(messages=msgs)
        result = CopilotAnswer(answer=text, citations=[], confidence=0.5, used_vendor_ids=[str(p.vendor_id) for p in proposals])

    return CopilotChatResponse(
        answer=result.answer,
        citations=[CopilotCitation(**c.model_dump()) for c in (result.citations or [])],
        confidence=result.confidence,
        used_vendor_ids=result.used_vendor_ids or [str(p.vendor_id) for p in proposals],
    )
