"""Proposal and ProposalDocument models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProposalStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    SCORING = "SCORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("procurement_projects.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    project_vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("project_vendors.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus, name="proposal_status"), default=ProposalStatus.UPLOADED, nullable=False, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposal_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    submitted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project_vendor: Mapped["ProjectVendor"] = relationship(back_populates="proposals")  # type: ignore[name-defined]
    documents: Mapped[List["ProposalDocument"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )
    pricing: Mapped[Optional["PricingDetail"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    score: Mapped[Optional["VendorScore"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    recommendation: Mapped[Optional["Recommendation"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    extracted_fields: Mapped[List["ExtractedField"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )
    risks: Mapped[List["Risk"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )
    missing_info: Mapped[List["MissingInformation"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )
    jobs: Mapped[List["AnalysisJob"]] = relationship(  # type: ignore[name-defined]
        back_populates="proposal", cascade="all, delete-orphan", lazy="selectin"
    )


class ProposalDocument(Base):
    __tablename__ = "proposal_documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(16), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proposal: Mapped[Proposal] = relationship(back_populates="documents")
