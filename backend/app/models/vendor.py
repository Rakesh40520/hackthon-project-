"""Vendor and ProjectVendor models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VendorStatus(str, enum.Enum):
    INVITED = "INVITED"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    SELECTED = "SELECTED"


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, name="vendor_status"), default=VendorStatus.INVITED, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project_links: Mapped[List["ProjectVendor"]] = relationship(  # type: ignore[name-defined]
        back_populates="vendor", cascade="all, delete-orphan", lazy="selectin"
    )


class ProjectVendor(Base):
    __tablename__ = "project_vendors"
    __table_args__ = (UniqueConstraint("project_id", "vendor_id", name="uq_project_vendor"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("procurement_projects.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, name="project_vendor_status"), default=VendorStatus.INVITED, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["ProcurementProject"] = relationship(back_populates="project_vendors")  # type: ignore[name-defined]
    vendor: Mapped[Vendor] = relationship(back_populates="project_links")
    proposals: Mapped[List["Proposal"]] = relationship(  # type: ignore[name-defined]
        back_populates="project_vendor", cascade="all, delete-orphan", lazy="selectin"
    )
