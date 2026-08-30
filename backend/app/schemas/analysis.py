"""Pricing, extracted fields, evaluations, risks, scores, recommendations."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from app.models.analysis import EvaluationStatus, RiskCategory, RiskSeverity
from app.schemas.common import ID, ORMBase


class PricingDetailOut(ORMBase):
    id: ID
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
    year1_total: Optional[float] = None
    year3_total: Optional[float] = None
    year5_total: Optional[float] = None
    recurring_annual_cost: Optional[float] = None
    pricing_model: Optional[str] = None
    billing_frequency: Optional[str] = None
    price_escalation_pct: Optional[float] = None
    assumptions: Optional[Dict[str, Any]] = None
    raw_breakdown: Optional[Dict[str, Any]] = None


class ExtractedFieldOut(ORMBase):
    id: ID
    field_name: str
    field_group: str
    value: Optional[str] = None
    value_type: str
    confidence: float
    is_fact: bool
    is_inferred: bool
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    source_quote: Optional[str] = None


class RequirementEvaluationOut(ORMBase):
    id: ID
    requirement_id: ID
    requirement_name: Optional[str] = None
    status: EvaluationStatus
    score: float
    reason: str
    confidence: float
    evidence_document: Optional[str] = None
    evidence_page: Optional[int] = None
    evidence_section: Optional[str] = None
    evidence_quote: Optional[str] = None
    evaluated_value: Optional[str] = None


class RiskOut(ORMBase):
    id: ID
    category: RiskCategory
    severity: RiskSeverity
    title: str
    description: str
    evidence_quote: Optional[str] = None
    evidence_document: Optional[str] = None
    evidence_page: Optional[int] = None
    recommendation: Optional[str] = None


class MissingInformationOut(ORMBase):
    id: ID
    field_name: str
    importance: str
    why_it_matters: Optional[str] = None


class ClarificationQuestionOut(ORMBase):
    id: ID
    question: str
    category: Optional[str] = None
    priority: str


class ScoringComponentOut(ORMBase):
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    explanation: Optional[str] = None


class VendorScoreOut(ORMBase):
    id: ID
    proposal_id: ID
    total_score: float
    price_score: float
    technical_score: float
    security_score: float
    support_score: float
    implementation_score: float
    contract_score: float
    is_eligible: bool
    ineligibility_reasons: Optional[List[str]] = None
    rank: Optional[int] = None
    components: List[ScoringComponentOut] = []
    notes: Optional[str] = None


class RecommendationOut(ORMBase):
    id: ID
    proposal_id: ID
    recommended: bool
    rank: Optional[int] = None
    summary: str
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    next_steps: List[str]
    decision: Optional[str] = None


class AnalysisJobOut(ORMBase):
    id: ID
    proposal_id: ID
    status: str
    current_stage: Optional[str] = None
    progress: int
    stage_message: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class ProposalDetailOut(ORMBase):
    id: ID
    project_id: ID
    vendor_id: ID
    project_vendor_id: ID
    title: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    proposal_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime] = None
    vendor_name: Optional[str] = None
    vendor_company: Optional[str] = None
    documents: List[Dict[str, Any]] = []
    pricing: Optional[PricingDetailOut] = None
    extracted_fields: List[ExtractedFieldOut] = []
    evaluations: List[RequirementEvaluationOut] = []
    risks: List[RiskOut] = []
    missing_info: List[MissingInformationOut] = []
    clarification_questions: List[ClarificationQuestionOut] = []
    score: Optional[VendorScoreOut] = None
    recommendation: Optional[RecommendationOut] = None
    current_job: Optional[AnalysisJobOut] = None