"""Mock provider - requirement evaluation, risk detection, missing info."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.ai.mock_provider import MockProvider
from app.ai.schemas import (
    Evidence,
    MissingInfoItem,
    MissingInfoList,
    RequirementEvaluationList,
    RequirementEvaluationResult,
    RiskItem,
    RiskList,
)


def _requirement_evals(text: str) -> RequirementEvaluationList:
    reqs: List[dict] = []
    idx = text.find("REQUIREMENTS_JSON:")
    if idx != -1:
        sub = text[idx + len("REQUIREMENTS_JSON:"):].strip()
        if sub.startswith("["):
            bracket_count = 0
            end_idx = -1
            for i, ch in enumerate(sub):
                if ch == "[":
                    bracket_count += 1
                elif ch == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            if end_idx != -1:
                try:
                    reqs = json.loads(sub[:end_idx])
                except Exception:
                    reqs = []
    if not reqs:
        for line in text.splitlines():
            mm = re.match(r"Requirement:\s*(.+?)\s*\|\s*keywords:\s*(.+)", line, flags=re.IGNORECASE)
            if mm:
                reqs.append({"name": mm.group(1).strip(), "keywords": [k.strip() for k in mm.group(2).split(",")]})
    evaluations: List[RequirementEvaluationResult] = []
    tl = text.lower()
    for r in reqs:
        name = r.get("name", "Requirement")
        kws = r.get("keywords") or [name]
        if any(kw.lower() in tl for kw in kws if kw):
            status = "MEETS"
            score = 95.0
            reason = f"Found explicit reference matching: {name}"
        else:
            status = "DOES_NOT_MEET"
            score = 20.0
            reason = f"No evidence for {name} in the proposal text."
        ev = MockProvider._evidence_for(text, [k for k in kws if k]) if status != "DOES_NOT_MEET" else Evidence()
        evaluations.append(
            RequirementEvaluationResult(
                requirement_name=name,
                status=status,  # type: ignore[arg-type]
                score=score,
                reason=reason,
                confidence=0.8 if status != "DOES_NOT_MEET" else 0.6,
                evaluated_value="YES" if status == "MEETS" else "NO",
                evidence=ev,
            )
        )
    return RequirementEvaluationList(evaluations=evaluations)


def _risks(text: str) -> RiskList:
    t = text.lower()
    risks: List[RiskItem] = []
    if "auto-renew" in t or "auto renew" in t:
        risks.append(RiskItem(
            category="CONTRACT", severity="MEDIUM", title="Auto-renewal clause",
            description="The contract appears to auto-renew. Verify opt-out window.",
            recommendation="Negotiate an explicit opt-out window and written notice requirement."
        ))
    if "price escalation" in t or "annual increase" in t or re.search(r"escalat\w+", t):
        risks.append(RiskItem(
            category="COMMERCIAL", severity="MEDIUM", title="Annual price escalation",
            description="Price may escalate annually; cap not specified.",
            recommendation="Negotiate an explicit escalation cap (e.g. CPI or 3-5%)."
        ))
    if "termination" in t and "penalty" in t:
        risks.append(RiskItem(
            category="CONTRACT", severity="HIGH", title="Termination penalties",
            description="Termination penalties are mentioned in the proposal.",
            recommendation="Request details of the penalty formula and ensure symmetry."
        ))
    if "sla" not in t:
        risks.append(RiskItem(
            category="CONTRACT", severity="HIGH", title="Missing SLA",
            description="No SLA referenced in the proposal.",
            recommendation="Require formal SLA with credits and reporting."
        ))
    if not MockProvider._bool_match(t, ["encryption at rest", "encrypted at rest", "at-rest encryption", "encryption in transit", "tls", "https", "ssl"]):
        risks.append(RiskItem(
            category="SECURITY", severity="HIGH", title="Encryption not clearly specified",
            description="No explicit reference to encryption at rest / in transit.",
            recommendation="Request explicit encryption controls and key management details."
        ))
    if not risks:
        risks.append(RiskItem(
            category="COMMERCIAL", severity="LOW",
            title="No significant risks detected",
            description="Heuristic scan did not flag common procurement risks.",
            recommendation="Conduct detailed manual review before contract award."
        ))
    return RiskList(risks=risks)


def _missing(text: str) -> MissingInfoList:
    t = text.lower()
    items: List[MissingInfoItem] = []
    if "rto" not in t or "rpo" not in t:
        items.append(MissingInfoItem(field_name="Disaster recovery RTO / RPO", importance="HIGH", why_it_matters="Required to assess recovery commitments."))
    if "data residency" not in t and "data location" not in t:
        items.append(MissingInfoItem(field_name="Data residency", importance="HIGH", why_it_matters="Required for regulatory compliance."))
    if "sla credit" not in t and "service credit" not in t:
        items.append(MissingInfoItem(field_name="SLA credit structure", importance="MEDIUM", why_it_matters="Determines financial remedies for downtime."))
    if "escalation" not in t and "price increase" not in t:
        items.append(MissingInfoItem(field_name="Annual price escalation", importance="MEDIUM", why_it_matters="Impacts multi-year TCO."))
    if "api" in t and "rate limit" not in t and "usage limit" not in t:
        items.append(MissingInfoItem(field_name="API usage limits / rate limits", importance="LOW", why_it_matters="Operational planning for integrations."))
    if not items:
        items.append(MissingInfoItem(field_name="Implementation timeline", importance="MEDIUM", why_it_matters="Required to assess rollout risk."))
    return MissingInfoList(items=items)