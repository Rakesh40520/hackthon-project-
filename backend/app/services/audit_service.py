"""Audit log helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog
from app.models.user import User


async def record_audit(
    db: AsyncSession,
    user: Optional[User],
    action: AuditAction,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        metadata_json=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry
