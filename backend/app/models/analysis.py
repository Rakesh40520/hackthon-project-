"""Analysis models: extracted fields, evidence, pricing."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvaluationStatus(str, enum.Enum):
    MEETS = "MEETS"
    PARTIALLY_MEETS = "PARTIALLY_MEETS"
    DOES_NOT_MEET = "DOES_NOT_MEET"
    UNKNOWN = "UNKNOWN"


class RiskCategory(str, enum.Enum):
    COMMERCIAL = "COMMERCIAL"
    TECHNICAL = "TECHNICAL"
    SECURITY = "SECURITY"
    CONTRACT = "CONTRACT"
    SUPPORT = "SUPPORT"
    COMPLIANCE = "COMPLIANCE"


class RiskSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    field_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    field_group: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), default="string", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_fact: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_inferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proposal: Mapped["Proposal"] = relationship(back_populates="extracted_fields")  # type: ignore[name-defined]


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PricingDetail(Base):
    __tablename__ = "pricing_details"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), unique=True
    )
    currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    annual_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    monthly_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    implementation_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    license_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    support_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    maintenance_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    training_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    migration_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    additional_fees: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    discounts: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    taxes: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    year1_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    year3_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    year5_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    recurring_annual_cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    pricing_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    billing_frequency: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    price_escalation_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    assumptions: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    raw_breakdown: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship(back_populates="pricing")  # type: ignore[name-defined]
