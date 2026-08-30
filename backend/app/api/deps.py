"""Common FastAPI dependencies."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User


async def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from X-Forwarded-For or remote address."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def get_user_agent(request: Request) -> Optional[str]:
    return request.headers.get("user-agent")
