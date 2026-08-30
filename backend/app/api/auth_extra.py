"""Authentication endpoints - refresh/logout/me/change-password."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import _build_token_response
from app.database import get_db
from app.models import User, UserRole
from app.models.user import RefreshToken
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    RefreshTokenRequest,
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

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login/oauth", response_model=None, include_in_schema=False)
async def login_oauth(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 password form for Swagger UI."""
    result = await db.execute(select(User).where(User.email == form.username.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    raw, hashed, expires = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed, expires_at=expires))
    await db.commit()
    await db.refresh(user)
    return _build_token_response(user, raw)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    h = hash_refresh_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == h, RefreshToken.revoked == False)  # noqa: E712
    )
    rt = result.scalar_one_or_none()
    if not rt or rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")
    access = create_access_token(user.id, extra={"role": user.role.value, "email": user.email})
    return AccessTokenResponse(access_token=access, expires_in=60 * 60 * 24)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    h = hash_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == h))
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()
    return None


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_active_user)):
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.name is not None:
        user.name = payload.name
    if payload.company is not None:
        user.company = payload.company
    if payload.role is not None and user.role == UserRole.ADMIN:
        user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return None
