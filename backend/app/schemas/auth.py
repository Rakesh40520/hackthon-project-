"""Authentication and user schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import ID, ORMBase


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    role: Optional[UserRole] = None

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if v != info.data.get("password"):
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMBase):
    id: ID
    name: str
    email: EmailStr
    company: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[UserRole] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int