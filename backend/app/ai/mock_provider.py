"""Deterministic mock provider used for demos/tests when no API key is configured.

Uses regex/keyword heuristics on proposal text and returns validated Pydantic
models. NEVER fabricates features; returns UNKNOWN/null when nothing is found.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Type

from pydantic import BaseModel

from app.ai.provider import AIProvider, ChatMessage
from app.ai.schemas import (
    ClarificationQuestionsResult,
    CopilotAnswer,
    Evidence,
    MissingInfoList,
    PricingAnalysis,
    RecommendationResult,
    RequirementEvaluationList,
    RiskList,
    TechnicalCapabilities,
    VendorInformation,
    VendorScoreResult,
)

logger = logging.getLogger(__name__)

CAPABILITY_KEYWORDS = {
    "api": ["rest api", " api ", "restful", "graphql"],
    "api_rest": ["rest api", "restful"],
    "api_graphql": ["graphql"],
    "api_soap": ["soap api", "soap "],
    "sso": ["sso", "single sign-on", "single sign on"],
    "oauth": ["oauth"],
    "saml": ["saml"],
    "encryption_at_rest": ["encryption at rest", "encrypted at rest", "at-rest encryption"],
    "encryption_in_transit": ["encryption in transit", "tls", "https", "ssl"],
    "cloud_deployment": ["cloud", "saas", "aws", "azure", "gcp"],
    "on_premise_deployment": ["on-premise", "on premise", "on-premises", "self-hosted"],
    "backup": ["backup", "backups"],
    "disaster_recovery": ["disaster recovery", " dr ", "rto", "rpo"],
    "monitoring": ["monitoring", "observability", "metrics", "logs"],
}

COMPLIANCE_KEYWORDS = ["soc 2", "soc2", "iso 27001", "iso27001", "gdpr", "hipaa", "pci", "pci-dss", "fedramp"]
INTEGRATION_KEYWORDS = ["slack", "salesforce", "jira", "github", "okta", "azure ad", "active directory", "sap", "oracle"]
DATABASE_KEYWORDS = ["postgresql", "postgres", "mysql", "mongodb", "mssql", "sql server", "dynamodb", "redis"]


class MockProvider(AIProvider):
    name = "mock"

    # ----------- helpers -----------
    @staticmethod
    def _bool_match(text: str, keywords: List[str]) -> bool:
        t = text.lower()
        return any(k.lower() in t for k in keywords)

    @staticmethod
    def _first_quote(text: str, keywords: List[str], window: int = 220) -> Optional[Evidence]:
        t = text
        for kw in keywords:
            idx = t.lower().find(kw.lower())
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(t), idx + window)
                return Evidence(document=None, section=None, quote=t[start:end].strip())
        return None

    @staticmethod
    def _find_money(text: str) -> List[float]:
        matches = re.findall(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kKmM]?)", text)
        out: List[float] = []
        for num, suffix in matches:
            try:
                v = float(num.replace(",", ""))
                if suffix.lower() == "k":
                    v *= 1_000
                elif suffix.lower() == "m":
                    v *= 1_000_000
                out.append(v)
            except ValueError:
                continue
        return out

    @staticmethod
    def _find_percentage(text: str, label_regex: str) -> Optional[float]:
        m = re.search(label_regex + r".{0,30}?([0-9]+(?:\.[0-9]+)?)\s*%", text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def _evidence_for(text: str, keywords: List[str]) -> Evidence:
        ev = MockProvider._first_quote(text, keywords) or Evidence()
        return ev

    # ----------- interface -----------
    async def complete(
        self,
        messages: List[ChatMessage],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseModel:
        from app.ai.mock_vendor import _vendor_info, _pricing, _technical
        from app.ai.mock_evaluation import _requirement_evals, _risks, _missing
        from app.ai.mock_scoring import _score, _recommendation, _clarifications, _copilot

        joined = "\n".join(m.content for m in messages if m.role == "user")
        if response_model is VendorInformation:
            return _vendor_info(joined)
        if response_model is PricingAnalysis:
            return _pricing(joined)
        if response_model is TechnicalCapabilities:
            return _technical(joined)
        if response_model is RequirementEvaluationList:
            return _requirement_evals(joined)
        if response_model is RiskList:
            return _risks(joined)
        if response_model is MissingInfoList:
            return _missing(joined)
        if response_model is VendorScoreResult:
            return _score(joined)
        if response_model is RecommendationResult:
            return _recommendation(joined)
        if response_model is ClarificationQuestionsResult:
            return _clarifications(joined)
        if response_model is CopilotAnswer:
            return _copilot(joined)
        return response_model.model_construct()

    async def chat(self, messages: List[ChatMessage], temperature: Optional[float] = None) -> str:
        joined = "\n".join(m.content for m in messages)
        return "Based on the submitted proposals:\n\n" + joined[:600]
