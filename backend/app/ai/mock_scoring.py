"""Mock provider - scoring, recommendation, clarifications, copilot."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.ai.schemas import (
    ClarificationQuestionsResult,
    CopilotAnswer,
    RecommendationResult,
    VendorScoreResult,
)


def _score(text: str) -> VendorScoreResult:
    ctx: Dict[str, Any] = {}
    m = re.search(r"SCORE_CONTEXT\s*:\s*(\{.*\})", text, flags=re.DOTALL)
    if m:
        try:
            ctx = json.loads(m.group(1))
        except Exception:
            ctx = {}
    return VendorScoreResult(
        price_score=float(ctx.get("price_score", 75)),
        technical_score=float(ctx.get("technical_score", 80)),
        security_score=float(ctx.get("security_score", 75)),
        support_score=float(ctx.get("support_score", 75)),
        implementation_score=float(ctx.get("implementation_score", 75)),
        contract_score=float(ctx.get("contract_score", 75)),
        ineligibility_reasons=list(ctx.get("ineligibility_reasons", []) or []),
        notes="Mock scoring based on aggregated context; objective, weighted.",
    )


def _recommendation(text: str) -> RecommendationResult:
    ctx: Dict[str, Any] = {}
    m = re.search(r"RECO_CONTEXT\s*:\s*(\{.*\})", text, flags=re.DOTALL)
    if m:
        try:
            ctx = json.loads(m.group(1))
        except Exception:
            ctx = {}
    score = float(ctx.get("score", 0))
    eligible = bool(ctx.get("eligible", True))
    strengths = ctx.get("strengths", []) or []
    weaknesses = ctx.get("weaknesses", []) or []
    summary = f"Vendor scored {score:.0f}/100 and is {'eligible' if eligible else 'ineligible'}."
    reasoning = (
        "Score is computed deterministically from configured weights, requirement "
        "evaluations, risk analysis, and pricing normalization. Strengths and weaknesses "
        "summarize where the vendor excels and where further negotiation or clarification "
        "is recommended."
    )
    return RecommendationResult(
        recommended=eligible and score >= 75,
        rank=ctx.get("rank"),
        summary=summary,
        reasoning=reasoning,
        strengths=strengths or ["Meets core mandatory requirements", "Competitive pricing"],
        weaknesses=weaknesses or ["Some non-mandatory requirements partially met"],
        next_steps=[
            "Request clarifications for missing information",
            "Negotiate commercial terms and SLAs",
            "Schedule technical deep-dive workshop",
        ],
        decision=("RECOMMENDED" if (eligible and score >= 75) else ("ACCEPTABLE_WITH_CAVEATS" if eligible else "INELIGIBLE")),
    )


def _clarifications(text: str) -> ClarificationQuestionsResult:
    missing: List[str] = []
    m = re.search(r"MISSING_FIELDS\s*:\s*(\[.*?\])", text, flags=re.DOTALL)
    if m:
        try:
            missing = json.loads(m.group(1))
        except Exception:
            missing = []
    questions: List[str] = []
    templates = {
        "Disaster recovery RTO / RPO": "What are your committed RTO and RPO targets, and are they documented in the SLA?",
        "Data residency": "Where will customer data be stored and processed, and can we restrict to specific regions?",
        "SLA credit structure": "What is the SLA credit structure for missed availability targets?",
        "Annual price escalation": "What is the maximum annual price escalation and how is it calculated?",
        "API usage limits / rate limits": "Are there API rate limits, and what are the overage charges if any?",
        "Implementation timeline": "What is the typical implementation timeline, and what is required from our side?",
    }
    for f in missing:
        q = templates.get(f)
        if q and q not in questions:
            questions.append(q)
    if not questions:
        questions = [
            "What is your standard implementation timeline?",
            "What SLA credits apply if availability targets are missed?",
            "How is customer data encrypted at rest and in transit?",
        ]
    return ClarificationQuestionsResult(questions=questions)


def _copilot(text: str) -> CopilotAnswer:
    return CopilotAnswer(
        answer="Based on the proposals in this project, here is what I found:\n\n" + text[:800],
        citations=[],
        confidence=0.6,
        used_vendor_ids=[],
    )
