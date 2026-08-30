"""Procurement project endpoints."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_client_ip, get_user_agent
from app.database import get_db
from app.models import (
    AuditAction,
    ProjectStatus,
    ProcurementProject,
    Proposal,
    Requirement,
    Vendor,
    ProjectVendor,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.security import get_current_active_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/projects", tags=["Projects"])


async def _populate_counts(db: AsyncSession, project: ProcurementProject) -> ProcurementProject:
    pv_count = await db.execute(
        select(func.count(ProjectVendor.id)).where(ProjectVendor.project_id == project.id)
    )
    p_count = await db.execute(
        select(func.count(Proposal.id)).where(Proposal.project_id == project.id)
    )
    r_count = await db.execute(
        select(func.count(Requirement.id)).where(Requirement.project_id == project.id)
    )
    project.vendor_count = pv_count.scalar() or 0
    project.proposal_count = p_count.scalar() or 0
    project.requirement_count = r_count.scalar() or 0
    return project


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    status_filter: Optional[ProjectStatus] = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ProcurementProject).order_by(ProcurementProject.created_at.desc())
    if status_filter:
        stmt = stmt.where(ProcurementProject.status == status_filter)
    res = await db.execute(stmt)
    projects = res.scalars().all()
    return [ProjectOut.model_validate(await _populate_counts(db, p)) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    project = ProcurementProject(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        budget=payload.budget,
        currency=payload.currency,
        deadline=payload.deadline,
        status=payload.status,
        created_by_id=user.id,
        weight_price=payload.weight_price,
        weight_technical=payload.weight_technical,
        weight_security=payload.weight_security,
        weight_support=payload.weight_support,
        weight_implementation=payload.weight_implementation,
        weight_contract=payload.weight_contract,
    )
    db.add(project)
    await db.flush()
    await record_audit(
        db, user, AuditAction.PROJECT_CREATE, "project", project.id,
        description=f"Project '{project.name}' created",
        ip_address=await get_client_ip(request),
    )
    await db.commit()
    await db.refresh(project)
    return ProjectOut.model_validate(await _populate_counts(db, project))


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut.model_validate(await _populate_counts(db, p))


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    data = payload.model_dump(exclude_unset=True)
    weights_changed = any(k.startswith("weight_") for k in data)
    for k, v in data.items():
        setattr(p, k, v)
    await record_audit(
        db, user,
        AuditAction.WEIGHTS_UPDATED if weights_changed else AuditAction.PROJECT_UPDATE,
        "project", p.id, metadata={"changes": list(data.keys())},
    )
    await db.commit()
    await db.refresh(p)
    return ProjectOut.model_validate(await _populate_counts(db, p))


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(ProcurementProject).where(ProcurementProject.id == project_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    await record_audit(db, user, AuditAction.PROJECT_DELETE, "project", p.id, description=p.name)
    await db.delete(p)
    await db.commit()
    return MessageResponse(message="Project deleted", success=True)
