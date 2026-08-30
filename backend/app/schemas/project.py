"""Project, requirement, vendor, proposal schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.models.project import ProjectStatus
from app.models.requirement import RequirementCategory, RequirementPriority
from app.models.vendor import VendorStatus
from app.schemas.common import ID, ORMBase


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    currency: str = "USD"
    deadline: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    weight_price: float = 0.30
    weight_technical: float = 0.25
    weight_security: float = 0.15
    weight_support: float = 0.10
    weight_implementation: float = 0.10
    weight_contract: float = 0.10

    @field_validator("weight_price", "weight_technical", "weight_security", "weight_support", "weight_implementation", "weight_contract")
    @classmethod
    def check_weights(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Weights must be between 0 and 1")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[ProjectStatus] = None
    weight_price: Optional[float] = None
    weight_technical: Optional[float] = None
    weight_security: Optional[float] = None
    weight_support: Optional[float] = None
    weight_implementation: Optional[float] = None
    weight_contract: Optional[float] = None


class ProjectOut(ORMBase):
    id: ID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    currency: str
    deadline: Optional[datetime] = None
    status: ProjectStatus
    weight_price: float
    weight_technical: float
    weight_security: float
    weight_support: float
    weight_implementation: float
    weight_contract: float
    created_by_id: ID
    created_at: datetime
    updated_at: datetime
    vendor_count: Optional[int] = 0
    proposal_count: Optional[int] = 0
    requirement_count: Optional[int] = 0


# ----- Requirement -----
class RequirementCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: RequirementCategory = RequirementCategory.TECHNICAL
    priority: RequirementPriority = RequirementPriority.MEDIUM
    weight: float = 1.0
    mandatory: bool = False
    expected_value: Optional[str] = None
    comparison_operator: Optional[str] = None
    order_index: int = 0


class RequirementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RequirementCategory] = None
    priority: Optional[RequirementPriority] = None
    weight: Optional[float] = None
    mandatory: Optional[bool] = None
    expected_value: Optional[str] = None
    comparison_operator: Optional[str] = None
    order_index: Optional[int] = None


class RequirementOut(ORMBase):
    id: ID
    project_id: ID
    name: str
    description: Optional[str] = None
    category: RequirementCategory
    priority: RequirementPriority
    weight: float
    mandatory: bool
    expected_value: Optional[str] = None
    comparison_operator: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime


# ----- Vendor -----
class VendorCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: VendorStatus = VendorStatus.INVITED


class VendorUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[VendorStatus] = None


class VendorOut(ORMBase):
    id: ID
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: VendorStatus
    created_at: datetime
    updated_at: datetime


class ProjectVendorCreate(BaseModel):
    vendor_id: str
    status: VendorStatus = VendorStatus.INVITED
    notes: Optional[str] = None


class ProjectVendorUpdate(BaseModel):
    status: Optional[VendorStatus] = None
    notes: Optional[str] = None


class ProjectVendorOut(ORMBase):
    id: ID
    project_id: ID
    vendor_id: ID
    status: VendorStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    vendor: Optional[VendorOut] = None
    proposal_count: Optional[int] = 0