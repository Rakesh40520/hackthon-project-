"""Procurement report generation (PDF / Excel)."""
from __future__ import annotations

import io
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AuditAction,
    EvaluationStatus,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    Recommendation,
    Requirement,
    RequirementEvaluation,
    Risk,
    VendorScore,
)
from app.models.user import User
from app.schemas.copilot import ReportRequest
from app.security import get_current_active_user
from app.services.audit_service import record_audit
from app.services.report_service import generate_pdf_report, generate_xlsx_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/{project_id}")
async def generate_report(
    project_id: uuid.UUID,
    payload: ReportRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    proj = (await db.execute(
        select(ProcurementProject)
        .options(selectinload(ProcurementProject.project_vendors).selectinload(ProjectVendor.vendor))
        .where(ProcurementProject.id == project_id)
    )).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather data
    prop_res = await db.execute(
        select(Proposal)
        .options(
            selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor),
            selectinload(Proposal.pricing),
            selectinload(Proposal.score).selectinload(VendorScore.components),
            selectinload(Proposal.recommendation),
            selectinload(Proposal.risks),
            selectinload(Proposal.missing_info),
        )
        .where(Proposal.project_id == project_id)
    )
    proposals = prop_res.scalars().all()
    reqs = (await db.execute(select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.order_index))).scalars().all()
    evaluations: Dict[str, List[RequirementEvaluation]] = {}
    for p in proposals:
        ev_res = await db.execute(
            select(RequirementEvaluation).where(RequirementEvaluation.proposal_id == p.id)
        )
        evaluations[str(p.id)] = ev_res.scalars().all()

    if payload.format == "xlsx":
        data = generate_xlsx_report(proj, proposals, reqs, evaluations)
        await record_audit(db, user, AuditAction.REPORT_EXPORTED, "project", project_id, description="XLSX")
        await db.commit()
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="procurement_{project_id}.xlsx"'},
        )
    # default PDF
    data = generate_pdf_report(proj, proposals, reqs, evaluations)
    await record_audit(db, user, AuditAction.REPORT_EXPORTED, "project", project_id, description="PDF")
    await db.commit()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="procurement_{project_id}.pdf"'},
    )
