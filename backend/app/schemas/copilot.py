"""Comparison, copilot, reports schemas."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.analysis import (
    PricingDetailOut,
    RequirementEvaluationOut,
    RiskOut,
    VendorScoreOut,
    RecommendationOut,
)


class ComparisonVendorRow(BaseModel):
    vendor_id: str
    vendor_name: str
    proposal_id: Optional[str] = None
    pricing: Optional[PricingDetailOut] = None
    score: Optional[VendorScoreOut] = None
    recommendation: Optional[RecommendationOut] = None
    risk_counts: Dict[str, int] = {}
    compliance_pct: float = 0.0
    meets_mandatory: int = 0
    total_mandatory: int = 0


class ComparisonOut(BaseModel):
    project_id: str
    project_name: str
    vendors: List[ComparisonVendorRow]
    weights: Dict[str, float]
    ranking: List[Dict[str, Any]]


# ----- Copilot -----
class CopilotMessage(BaseModel):
    role: str  # user / assistant / system
    content: str


class CopilotChatRequest(BaseModel):
    project_id: str
    messages: List[CopilotMessage]
    vendor_id: Optional[str] = None


class CopilotCitation(BaseModel):
    document: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None


class CopilotChatResponse(BaseModel):
    answer: str
    citations: List[CopilotCitation] = []
    confidence: float = 0.0
    used_vendor_ids: List[str] = []


# ----- Reports -----
class ReportRequest(BaseModel):
    project_id: str
    format: str = "pdf"  # pdf | xlsx
    include_sections: Optional[List[str]] = None
