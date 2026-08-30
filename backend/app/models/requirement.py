"""Requirement model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RequirementCategory(str, enum.Enum):
    TECHNICAL = "TECHNICAL"
    COMMERCIAL = "COMMERCIAL"
    BUSINESS = "BUSINESS"
    SECURITY = "SECURITY"
    SUPPORT = "SUPPORT"
    COMPLIANCE = "COMPLIANCE"


class RequirementPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("procurement_projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[RequirementCategory] = mapped_column(
        Enum(RequirementCategory, name="requirement_category"), default=RequirementCategory.TECHNICAL, nullable=False, index=True
    )
    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(RequirementPriority, name="requirement_priority"), default=RequirementPriority.MEDIUM, nullable=False, index=True
    )
    weight: Mapped[float] = mapped_column(Numeric(6, 4), default=1.0, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparison_operator: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # eq, gt, lt, gte, lte, contains
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["ProcurementProject"] = relationship(back_populates="requirements")  # type: ignore[name-defined]
    evaluations: Mapped[List["RequirementEvaluation"]] = relationship(  # type: ignore[name-defined]
        back_populates="requirement", cascade="all, delete-orphan", lazy="selectin"
    )
