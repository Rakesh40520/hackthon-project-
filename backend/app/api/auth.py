"""Authentication endpoints - register/login."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_user_agent
from app.config import settings
from app.database import get_db
from app.models import AuditAction, User, UserRole
from app.models.user import RefreshToken
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token_response(user: User, refresh_raw: str) -> TokenResponse:
    access = create_access_token(user.id, extra={"role": user.role.value, "email": user.email})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        company=payload.company,
        hashed_password=hash_password(payload.password),
        role=payload.role or UserRole.PROCUREMENT_MANAGER,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    raw, hashed, expires = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed, expires_at=expires))
    await db.commit()
    await db.refresh(user)

    await record_audit(
        db, user, AuditAction.USER_REGISTER, "user", user.id,
        description=f"User {user.email} registered",
        ip_address=await get_client_ip(request),
        user_agent=await get_user_agent(request),
    )
    await db.commit()
    return _build_token_response(user, raw)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    user.last_login_at = datetime.now(timezone.utc)
    raw, hashed, expires = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id, token_hash=hashed, expires_at=expires,
        ip_address=await get_client_ip(request), user_agent=await get_user_agent(request),
    ))
    await record_audit(
        db, user, AuditAction.USER_LOGIN, "user", user.id,
        ip_address=await get_client_ip(request),
        user_agent=await get_user_agent(request),
    )
    await db.commit()
    await db.refresh(user)
    return _build_token_response(user, raw)
