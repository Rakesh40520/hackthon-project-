"""Risk and missing information models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.analysis import RiskCategory, RiskSeverity


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[RiskCategory] = mapped_column(
        Enum(RiskCategory, name="risk_category"), default=RiskCategory.COMMERCIAL, nullable=False, index=True
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, name="risk_severity"), default=RiskSeverity.MEDIUM, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proposal: Mapped["Proposal"] = relationship(back_populates="risks")  # type: ignore[name-defined]


class MissingInformation(Base):
    __tablename__ = "missing_information"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    importance: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    why_it_matters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proposal: Mapped["Proposal"] = relationship(back_populates="missing_info")  # type: ignore[name-defined]
