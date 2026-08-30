"""Proposal list and upload endpoints."""
from __future__ import annotations

import hashlib
import os
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_client_ip
from app.config import settings
from app.database import get_db
from app.models import (
    AnalysisJob,
    AuditAction,
    JobStatus,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    ProposalDocument,
    ProposalStatus,
    VendorScore,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.proposal import ProposalOut
from app.security import get_current_active_user
from app.services.audit_service import record_audit
from app.services.job_service import get_or_create_job
from app.utils.storage import get_storage

router = APIRouter(prefix="/proposals", tags=["Proposals"])


def _ext_from_filename(name: str) -> str:
    return os.path.splitext(name)[1].lower()


@router.get("", response_model=List[ProposalOut])
async def list_proposals(
    project_id: Optional[uuid.UUID] = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Proposal)
        .options(
            selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor),
            selectinload(Proposal.score),
        )
        .order_by(desc(Proposal.created_at))
    )
    if project_id:
        stmt = stmt.where(Proposal.project_id == project_id)
    res = await db.execute(stmt)
    rows: List[ProposalOut] = []
    for p in res.scalars().all():
        out = ProposalOut.model_validate(p)
        if p.project_vendor and p.project_vendor.vendor:
            out.vendor_name = p.project_vendor.vendor.company_name
            out.vendor_company = p.project_vendor.vendor.company_name
        if p.score:
            out.score = p.score.total_score
            out.rank = p.score.rank
        rows.append(out)
    return rows


@router.post("/upload", response_model=ProposalOut, status_code=status.HTTP_201_CREATED)
async def upload_proposal(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: str = Form(...),
    vendor_id: str = Form(...),
    title: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    ext = _ext_from_filename(file.filename or "")
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
    content = await file.read()
    size = len(content)
    if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    proj = (await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    pv = (
        await db.execute(
            select(ProjectVendor)
            .where(ProjectVendor.project_id == project_id, ProjectVendor.vendor_id == vendor_id)
        )
    ).scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Vendor not linked to project")

    storage = get_storage()
    storage_path, _ = storage.save_bytes(str(project_id), str(vendor_id), file.filename or "proposal", content)
    checksum = hashlib.sha256(content).hexdigest()

    proposal = Proposal(
        project_id=project_id, vendor_id=vendor_id, project_vendor_id=pv.id,
        title=title or f"Proposal from {pv.vendor.company_name if pv.vendor else 'vendor'}",
        status=ProposalStatus.QUEUED, progress=0, submitted_by=user.id,
    )
    db.add(proposal)
    await db.flush()
    doc = ProposalDocument(
        proposal_id=proposal.id, filename=file.filename or "proposal",
        storage_path=storage_path, file_size=size,
        mime_type=file.content_type or "application/octet-stream",
        file_extension=ext, checksum=checksum,
    )
    db.add(doc)
    job = await get_or_create_job(db, str(proposal.id))
    job.status = JobStatus.PENDING
    job.progress = 0
    job.stage_message = "Queued"
    await record_audit(
        db, user, AuditAction.PROPOSAL_UPLOAD, "proposal", proposal.id,
        description=f"Uploaded {file.filename}",
        ip_address=await get_client_ip(request),
        metadata={"size": size, "checksum": checksum},
    )
    await db.commit()
    await db.refresh(proposal)
    background_tasks.add_task(_safe_run, str(proposal.id))

    out = ProposalOut.model_validate(proposal)
    if pv.vendor:
        out.vendor_name = pv.vendor.company_name
        out.vendor_company = pv.vendor.company_name
    return out


async def _safe_run(proposal_id: str) -> None:
    from app.database import AsyncSessionLocal
    from app.services.analysis_orchestrator import run_full_analysis
    import logging
    try:
        async with AsyncSessionLocal() as db:
            await run_full_analysis(db, proposal_id)
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).exception("Background analysis failed: %s", e)