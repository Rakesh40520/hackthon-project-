"""Common Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

ID = Union[uuid.UUID, str]


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 50


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class IDResponse(BaseModel):
    id: ID


class TimestampedResponse(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str
    time: datetime = Field(default_factory=datetime.utcnow)