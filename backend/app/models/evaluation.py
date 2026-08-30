"""Evaluation, risk, scoring, recommendation models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.analysis import EvaluationStatus, RiskCategory, RiskSeverity


class RequirementEvaluation(Base):
    __tablename__ = "requirement_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("requirements.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="evaluation_status"), default=EvaluationStatus.UNKNOWN, nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship()  # type: ignore[name-defined]
    requirement: Mapped["Requirement"] = relationship(back_populates="evaluations")  # type: ignore[name-defined]
