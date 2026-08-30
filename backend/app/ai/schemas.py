"""Pydantic schemas used for structured AI output."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EvaluationStatusStr = Literal["MEETS", "PARTIALLY_MEETS", "DOES_NOT_MEET", "UNKNOWN"]
RiskCategoryStr = Literal["COMMERCIAL", "TECHNICAL", "SECURITY", "CONTRACT", "SUPPORT", "COMPLIANCE"]
RiskSeverityStr = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Evidence(BaseModel):
    document: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None


class ExtractedFieldAI(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence: Evidence = Field(default_factory=Evidence)
    is_fact: bool = True
    is_inferred: bool = False


class VendorInformation(BaseModel):
    vendor_name: Optional[str] = None
    proposal_date: Optional[str] = None
    valid_until: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    fields: List[ExtractedFieldAI] = Field(default_factory=list)


class PricingAnalysis(BaseModel):
    currency: Optional[str] = None
    total_cost: Optional[float] = None
    annual_cost: Optional[float] = None
    monthly_cost: Optional[float] = None
    implementation_cost: Optional[float] = None
    license_cost: Optional[float] = None
    support_cost: Optional[float] = None
    maintenance_cost: Optional[float] = None
    training_cost: Optional[float] = None
    migration_cost: Optional[float] = None
    additional_fees: Optional[float] = None
    discounts: Optional[float] = None
    taxes: Optional[float] = None
    pricing_model: Optional[str] = None
    billing_frequency: Optional[str] = None
    price_escalation_pct: Optional[float] = None
    year1_total: Optional[float] = None
    year3_total: Optional[float] = None
    year5_total: Optional[float] = None
    recurring_annual_cost: Optional[float] = None
    assumptions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    fields: List[ExtractedFieldAI] = Field(default_factory=list)


class TechnicalCapabilities(BaseModel):
    api: Optional[bool] = None
    sso: Optional[bool] = None
    oauth: Optional[bool] = None
    saml: Optional[bool] = None
    encryption_at_rest: Optional[bool] = None
    encryption_in_transit: Optional[bool] = None
    cloud_deployment: Optional[bool] = None
    on_premise_deployment: Optional[bool] = None
    sla_percentage: Optional[float] = None
    max_concurrent_users: Optional[int] = None
    backup: Optional[bool] = None
    disaster_recovery: Optional[bool] = None
    monitoring: Optional[bool] = None
    api_rest: Optional[bool] = None
    api_graphql: Optional[bool] = None
    api_soap: Optional[bool] = None
    integrations: List[str] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    database_support: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    fields: List[ExtractedFieldAI] = Field(default_factory=list)


class RequirementEvaluationResult(BaseModel):
    requirement_name: str
    status: EvaluationStatusStr
    score: float = Field(0.0, ge=0.0, le=100.0)
    reason: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evaluated_value: Optional[str] = None
    evidence: Evidence = Field(default_factory=Evidence)


class RequirementEvaluationList(BaseModel):
    evaluations: List[RequirementEvaluationResult]


class RiskItem(BaseModel):
    category: RiskCategoryStr
    severity: RiskSeverityStr
    title: str
    description: str
    evidence_quote: Optional[str] = None
    evidence_document: Optional[str] = None
    evidence_page: Optional[int] = None
    recommendation: Optional[str] = None


class RiskList(BaseModel):
    risks: List[RiskItem]


class MissingInfoItem(BaseModel):
    field_name: str
    importance: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    why_it_matters: Optional[str] = None


class MissingInfoList(BaseModel):
    items: List[MissingInfoItem]


class VendorScoreResult(BaseModel):
    price_score: float = Field(0.0, ge=0.0, le=100.0)
    technical_score: float = Field(0.0, ge=0.0, le=100.0)
    security_score: float = Field(0.0, ge=0.0, le=100.0)
    support_score: float = Field(0.0, ge=0.0, le=100.0)
    implementation_score: float = Field(0.0, ge=0.0, le=100.0)
    contract_score: float = Field(0.0, ge=0.0, le=100.0)
    ineligibility_reasons: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RecommendationResult(BaseModel):
    recommended: bool
    rank: Optional[int] = None
    summary: str
    reasoning: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    decision: Optional[str] = None


class ClarificationQuestionsResult(BaseModel):
    questions: List[str] = Field(default_factory=list)


class CopilotAnswer(BaseModel):
    answer: str
    citations: List[Evidence] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    used_vendor_ids: List[str] = Field(default_factory=list)
