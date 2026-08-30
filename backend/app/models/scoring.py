"""Vendor score, recommendation, clarification models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScoringComponent(Base):
    __tablename__ = "scoring_components"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    score_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("vendor_scores.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    score: Mapped["VendorScore"] = relationship(back_populates="components")


class VendorScore(Base):
    __tablename__ = "vendor_scores"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), unique=True
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    price_score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[float] = mapped_column(Float, nullable=False)
    security_score: Mapped[float] = mapped_column(Float, nullable=False)
    support_score: Mapped[float] = mapped_column(Float, nullable=False)
    implementation_score: Mapped[float] = mapped_column(Float, nullable=False)
    contract_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ineligibility_reasons: Mapped[Optional[list]] = mapped_column(JSONBCompat(), nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship(back_populates="score")  # type: ignore[name-defined]
    components: Mapped[List[ScoringComponent]] = relationship(
        back_populates="score", cascade="all, delete-orphan", lazy="selectin"
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), unique=True
    )
    recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, default="", nullable=False)
    strengths: Mapped[list] = mapped_column(JSONBCompat(), default=list, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JSONBCompat(), default=list, nullable=False)
    next_steps: Mapped[list] = mapped_column(JSONBCompat(), default=list, nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship(back_populates="recommendation")  # type: ignore[name-defined]


class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)