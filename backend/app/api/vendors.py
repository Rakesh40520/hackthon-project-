"""Global vendor directory endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditAction, Vendor, VendorStatus
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import VendorCreate, VendorOut, VendorUpdate
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[VendorOut])
async def list_vendors(
    q: Optional[str] = None,
    industry: Optional[str] = None,
    status_filter: Optional[VendorStatus] = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Vendor).order_by(Vendor.company_name.asc())
    if q:
        stmt = stmt.where(Vendor.company_name.ilike(f"%{q}%"))
    if industry:
        stmt = stmt.where(Vendor.industry == industry)
    if status_filter:
        stmt = stmt.where(Vendor.status == status_filter)
    res = await db.execute(stmt)
    return [VendorOut.model_validate(v) for v in res.scalars().all()]


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    v = Vendor(**payload.model_dump())
    db.add(v)
    await db.flush()
    await record_audit(db, user, AuditAction.VENDOR_CREATE, "vendor", v.id, description=v.company_name)
    await db.commit()
    await db.refresh(v)
    return VendorOut.model_validate(v)


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(vendor_id: uuid.UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorOut.model_validate(v)


@router.patch("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: uuid.UUID,
    payload: VendorUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    await record_audit(db, user, AuditAction.VENDOR_UPDATE, "vendor", v.id)
    await db.commit()
    await db.refresh(v)
    return VendorOut.model_validate(v)


@router.delete("/{vendor_id}", response_model=MessageResponse)
async def delete_vendor(vendor_id: uuid.UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await record_audit(db, user, AuditAction.VENDOR_UPDATE, "vendor", v.id, description="Vendor deleted")
    await db.delete(v)
    await db.commit()
    return MessageResponse(message="Vendor deleted", success=True)
