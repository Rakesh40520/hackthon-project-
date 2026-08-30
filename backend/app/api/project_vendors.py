"""Project-vendor linking endpoints."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    AuditAction,
    Proposal,
    ProjectVendor,
    Vendor,
    VendorStatus,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import (
    ProjectVendorCreate,
    ProjectVendorOut,
    ProjectVendorUpdate,
    VendorOut,
)
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/projects/{project_id}/vendors", tags=["Project Vendors"])


@router.get("", response_model=List[ProjectVendorOut])
async def list_project_vendors(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ProjectVendor)
        .where(ProjectVendor.project_id == project_id)
        .options(selectinload(ProjectVendor.vendor))
        .order_by(ProjectVendor.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()
    out: List[ProjectVendorOut] = []
    for pv in rows:
        c = await db.execute(select(func.count(Proposal.id)).where(Proposal.project_vendor_id == pv.id))
        data = ProjectVendorOut.model_validate(pv)
        data.vendor = VendorOut.model_validate(pv.vendor) if pv.vendor else None
        data.proposal_count = c.scalar() or 0
        out.append(data)
    return out


@router.post("", response_model=ProjectVendorOut, status_code=status.HTTP_201_CREATED)
async def add_project_vendor(
    project_id: uuid.UUID,
    payload: ProjectVendorCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Vendor).where(Vendor.id == payload.vendor_id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vendor not found")
    existing = await db.execute(
        select(ProjectVendor).where(
            ProjectVendor.project_id == project_id,
            ProjectVendor.vendor_id == payload.vendor_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vendor already added to project")

    pv = ProjectVendor(
        project_id=project_id,
        vendor_id=payload.vendor_id,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(pv)
    await db.flush()
    await record_audit(db, user, AuditAction.VENDOR_CREATE, "project_vendor", pv.id, description="Added to project")
    await db.commit()
    pv = (await db.execute(
        select(ProjectVendor).where(ProjectVendor.id == pv.id).options(selectinload(ProjectVendor.vendor))
    )).scalar_one()
    out = ProjectVendorOut.model_validate(pv)
    out.vendor = VendorOut.model_validate(pv.vendor) if pv.vendor else None
    out.proposal_count = 0
    return out


@router.patch("/{pv_id}", response_model=ProjectVendorOut)
async def update_project_vendor(
    project_id: uuid.UUID,
    pv_id: uuid.UUID,
    payload: ProjectVendorUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ProjectVendor)
        .where(ProjectVendor.id == pv_id, ProjectVendor.project_id == project_id)
        .options(selectinload(ProjectVendor.vendor))
    )
    pv = res.scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Project-vendor link not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(pv, k, v)
    if payload.status is not None:
        action = {
            VendorStatus.SHORTLISTED: AuditAction.VENDOR_SHORTLISTED,
            VendorStatus.SELECTED: AuditAction.VENDOR_SELECTED,
            VendorStatus.REJECTED: AuditAction.VENDOR_REJECTED,
        }.get(payload.status, AuditAction.VENDOR_UPDATE)
        await record_audit(db, user, action, "project_vendor", pv.id)
    await db.commit()
    out = ProjectVendorOut.model_validate(pv)
    out.vendor = VendorOut.model_validate(pv.vendor) if pv.vendor else None
    return out


@router.delete("/{pv_id}", response_model=MessageResponse)
async def remove_project_vendor(
    project_id: uuid.UUID,
    pv_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ProjectVendor).where(ProjectVendor.id == pv_id, ProjectVendor.project_id == project_id)
    )
    pv = res.scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Project-vendor link not found")
    await db.delete(pv)
    await db.commit()
    return MessageResponse(message="Removed from project", success=True)
