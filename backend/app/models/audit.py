"""Audit log model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditAction(str, enum.Enum):
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    PROJECT_CREATE = "PROJECT_CREATE"
    PROJECT_UPDATE = "PROJECT_UPDATE"
    PROJECT_DELETE = "PROJECT_DELETE"
    REQUIREMENT_CREATE = "REQUIREMENT_CREATE"
    REQUIREMENT_UPDATE = "REQUIREMENT_UPDATE"
    REQUIREMENT_DELETE = "REQUIREMENT_DELETE"
    VENDOR_CREATE = "VENDOR_CREATE"
    VENDOR_UPDATE = "VENDOR_UPDATE"
    PROPOSAL_UPLOAD = "PROPOSAL_UPLOAD"
    PROPOSAL_DELETE = "PROPOSAL_DELETE"
    ANALYSIS_START = "ANALYSIS_START"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    ANALYSIS_FAIL = "ANALYSIS_FAIL"
    SCORE_COMPUTED = "SCORE_COMPUTED"
    WEIGHTS_UPDATED = "WEIGHTS_UPDATED"
    RECOMMENDATION_GENERATED = "RECOMMENDATION_GENERATED"
    CLARIFICATION_GENERATED = "CLARIFICATION_GENERATED"
    VENDOR_SHORTLISTED = "VENDOR_SHORTLISTED"
    VENDOR_SELECTED = "VENDOR_SELECTED"
    VENDOR_REJECTED = "VENDOR_REJECTED"
    REPORT_EXPORTED = "REPORT_EXPORTED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped[Optional["User"]] = relationship()  # type: ignore[name-defined]
