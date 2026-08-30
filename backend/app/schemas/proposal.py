"""Proposal, analysis, comparison, recommendation schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.models.analysis import EvaluationStatus, RiskCategory, RiskSeverity
from app.models.proposal import ProposalStatus
from app.schemas.common import ID, ORMBase


class ProposalCreate(BaseModel):
    project_id: str
    vendor_id: str
    title: str
    proposal_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class ProposalOut(ORMBase):
    id: ID
    project_id: ID
    vendor_id: ID
    project_vendor_id: ID
    title: str
    status: ProposalStatus
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    proposal_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    submitted_by: Optional[ID] = None
    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime] = None
    vendor_name: Optional[str] = None
    vendor_company: Optional[str] = None
    score: Optional[float] = None
    rank: Optional[int] = None

    @field_validator("score", mode="before")
    @classmethod
    def extract_score(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if hasattr(v, "total_score"):
            return float(v.total_score)
        return None

    @field_validator("rank", mode="before")
    @classmethod
    def extract_rank(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if hasattr(v, "rank"):
            return getattr(v, "rank")
        return None


class ProposalDocumentOut(ORMBase):
    id: ID
    filename: str
    storage_path: str
    file_size: int
    mime_type: str
    file_extension: str
    page_count: Optional[int] = None
    created_at: datetime


from app.schemas.analysis import (
    AnalysisJobOut,
    ClarificationQuestionOut,
    ExtractedFieldOut,
    MissingInformationOut,
    PricingDetailOut,
    ProposalDetailOut,
    RecommendationOut,
    RequirementEvaluationOut,
    RiskOut,
    ScoringComponentOut,
    VendorScoreOut,
)

__all__ = [
    "ProposalCreate",
    "ProposalOut",
    "ProposalDocumentOut",
    "AnalysisJobOut",
    "ClarificationQuestionOut",
    "ExtractedFieldOut",
    "MissingInformationOut",
    "PricingDetailOut",
    "ProposalDetailOut",
    "RecommendationOut",
    "RequirementEvaluationOut",
    "RiskOut",
    "ScoringComponentOut",
    "VendorScoreOut",
]