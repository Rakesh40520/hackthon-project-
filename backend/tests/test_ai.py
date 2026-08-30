"""AI provider mock tests."""
from __future__ import annotations

import asyncio
import json
import pytest

from app.ai import (
    ClarificationQuestionsResult,
    CopilotAnswer,
    MissingInfoList,
    PricingAnalysis,
    RecommendationResult,
    RequirementEvaluationList,
    RiskList,
    TechnicalCapabilities,
    VendorInformation,
    VendorScoreResult,
    get_ai_provider,
)
from app.ai.provider import ChatMessage


def test_factory_returns_mock():
    p = get_ai_provider()
    assert p.name == "mock"


@pytest.mark.asyncio
async def test_vendor_info_extraction():
    p = get_ai_provider()
    res = await p.complete(
        messages=[ChatMessage(role="user", content="Proposal from Acme Cloud dated 2026-01-01")],
        response_model=VendorInformation,
    )
    assert res.vendor_name
    assert "Acme" in (res.vendor_name or "")


@pytest.mark.asyncio
async def test_pricing_extraction():
    p = get_ai_provider()
    text = "The cost is $120,000 per year. Implementation $20,000. License $50,000."
    res = await p.complete(
        messages=[ChatMessage(role="user", content=text)],
        response_model=PricingAnalysis,
    )
    assert res.annual_cost is not None
    assert res.implementation_cost is not None


@pytest.mark.asyncio
async def test_requirement_evaluation():
    p = get_ai_provider()
    req_payload = [{"name": "SSO", "keywords": ["sso", "saml"]}]
    text = "Our platform supports SSO via SAML 2.0 with optional MFA."
    res = await p.complete(
        messages=[ChatMessage(role="user", content=f"REQUIREMENTS_JSON: {json.dumps(req_payload)}\n\n{text}")],
        response_model=RequirementEvaluationList,
    )
    assert res.evaluations[0].status == "MEETS"
