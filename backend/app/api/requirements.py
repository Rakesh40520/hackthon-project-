"""Requirement endpoints."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AuditAction,
    ProcurementProject,
    Requirement,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import (
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
)
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["Requirements"])


async def _ensure_project(db: AsyncSession, project_id: uuid.UUID) -> ProcurementProject:
    res = await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("", response_model=List[RequirementOut])
async def list_requirements(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_project(db, project_id)
    res = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.order_index, Requirement.created_at)
    )
    return [RequirementOut.model_validate(r) for r in res.scalars().all()]


@router.post("", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: uuid.UUID,
    payload: RequirementCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_project(db, project_id)
    r = Requirement(project_id=project_id, **payload.model_dump())
    db.add(r)
    await db.flush()
    await record_audit(db, user, AuditAction.REQUIREMENT_CREATE, "requirement", r.id, description=r.name)
    await db.commit()
    await db.refresh(r)
    return RequirementOut.model_validate(r)


@router.patch("/{requirement_id}", response_model=RequirementOut)
async def update_requirement(
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    payload: RequirementUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id, Requirement.project_id == project_id)
    )
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    await record_audit(db, user, AuditAction.REQUIREMENT_UPDATE, "requirement", r.id)
    await db.commit()
    await db.refresh(r)
    return RequirementOut.model_validate(r)


@router.delete("/{requirement_id}", response_model=MessageResponse)
async def delete_requirement(
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id, Requirement.project_id == project_id)
    )
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    await record_audit(db, user, AuditAction.REQUIREMENT_DELETE, "requirement", r.id, description=r.name)
    await db.delete(r)
    await db.commit()
    return MessageResponse(message="Requirement deleted", success=True)


# Convenience: also a non-nested endpoint
@router.get("/all", response_model=List[RequirementOut], include_in_schema=False)
async def list_all_requirements_alt(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_requirements(project_id=project_id, user=user, db=db)
