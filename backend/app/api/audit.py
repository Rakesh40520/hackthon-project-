"""Audit log endpoint."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AuditAction, AuditLog
from app.models.user import User
from app.schemas.common import Page
from app.security import get_current_active_user

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
async def list_audit(
    action: Optional[AuditAction] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).options(selectinload(AuditLog.user)).order_by(desc(AuditLog.created_at))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    total = (await db.execute(select(AuditLog.id))).scalars().all()
    total_count = len(total)
    offset = (page - 1) * page_size
    res = await db.execute(stmt.offset(offset).limit(page_size))
    items = []
    for log in res.scalars().all():
        items.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "user_name": log.user.name if log.user else None,
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "description": log.description,
            "metadata": log.metadata_json,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        })
    return {"items": items, "total": total_count, "page": page, "page_size": page_size}
