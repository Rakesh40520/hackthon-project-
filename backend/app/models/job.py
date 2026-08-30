"""Background analysis job tracking."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from app.db_types import GUID, JSONBCompat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStage(str, enum.Enum):
    UPLOAD = "UPLOAD"
    EXTRACT = "EXTRACT"
    ANALYZE = "ANALYZE"
    EVALUATE_REQUIREMENTS = "EVALUATE_REQUIREMENTS"
    ANALYZE_RISKS = "ANALYZE_RISKS"
    SCORE = "SCORE"
    RECOMMEND = "RECOMMEND"
    FINALIZE = "FINALIZE"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("proposals.id", ondelete="CASCADE"), index=True
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.PENDING, nullable=False, index=True
    )
    current_stage: Mapped[Optional[JobStage]] = mapped_column(
        Enum(JobStage, name="job_stage"), nullable=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stage_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONBCompat(), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposal: Mapped["Proposal"] = relationship(back_populates="jobs")  # type: ignore[name-defined]
