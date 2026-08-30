"""Procurement Project model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EVALUATION = "EVALUATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProcurementProject(Base):
    __tablename__ = "procurement_projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    budget: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"), default=ProjectStatus.DRAFT, nullable=False, index=True
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Default scoring weights
    weight_price: Mapped[float] = mapped_column(Numeric(6, 4), default=0.30, nullable=False)
    weight_technical: Mapped[float] = mapped_column(Numeric(6, 4), default=0.25, nullable=False)
    weight_security: Mapped[float] = mapped_column(Numeric(6, 4), default=0.15, nullable=False)
    weight_support: Mapped[float] = mapped_column(Numeric(6, 4), default=0.10, nullable=False)
    weight_implementation: Mapped[float] = mapped_column(Numeric(6, 4), default=0.10, nullable=False)
    weight_contract: Mapped[float] = mapped_column(Numeric(6, 4), default=0.10, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="projects", foreign_keys=[created_by_id])  # type: ignore[name-defined]
    requirements: Mapped[List["Requirement"]] = relationship(  # type: ignore[name-defined]
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    project_vendors: Mapped[List["ProjectVendor"]] = relationship(  # type: ignore[name-defined]
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
