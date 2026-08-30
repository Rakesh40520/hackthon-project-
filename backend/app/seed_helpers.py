"""Seed helpers: ensure user/project/vendors/requirements/proposals."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ProcurementProject,
    ProjectStatus,
    ProjectVendor,
    Proposal,
    ProposalStatus,
    ProposalDocument,
    Requirement,
    User,
    UserRole,
    Vendor,
    VendorStatus,
)
from app.security import hash_password


SAMPLE_REQS = [
    ("99.9% minimum SLA", "Vendor must commit to 99.9% uptime with credits", "TECHNICAL", "CRITICAL", True),
    ("SSO support", "Must support SAML or OIDC SSO", "SECURITY", "CRITICAL", True),
    ("REST API", "Expose comprehensive REST API for automation", "TECHNICAL", "HIGH", True),
    ("Encryption at rest", "AES-256 at rest", "SECURITY", "CRITICAL", True),
    ("Encryption in transit", "TLS 1.2+", "SECURITY", "CRITICAL", True),
    ("24/7 support", "24/7 critical-incident support", "SUPPORT", "HIGH", False),
    ("Maximum $500,000 annual budget", "Total annual cost must not exceed USD 500,000", "COMMERCIAL", "HIGH", True),
    ("Implementation under 90 days", "<= 90 days", "BUSINESS", "HIGH", False),
    ("SOC 2 Type II compliance", "Current SOC 2 Type II report", "COMPLIANCE", "HIGH", True),
    ("PostgreSQL support", "Native PostgreSQL compatibility", "TECHNICAL", "MEDIUM", False),
    ("DR with RTO < 4h", "DR RTO below 4 hours", "TECHNICAL", "HIGH", True),
    ("Multi-region deployment", "Active or passive multi-region", "TECHNICAL", "MEDIUM", False),
]

VENDORS = [
    ("AWS (Amazon Web Services)", "AWS Sales", "aws-sales@example.com", "Cloud"),
    ("Microsoft Azure", "Azure Sales", "azure-sales@example.com", "Cloud"),
    ("Google Cloud Platform", "GCP Sales", "gcp-sales@example.com", "Cloud"),
]


async def ensure_user(db: AsyncSession) -> User:
    res = await db.execute(select(User).where(User.email == "admin@procurement.dev"))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(
        name="Demo Admin", email="admin@procurement.dev", company="Demo Corp",
        hashed_password=hash_password("Admin123!"),
        role=UserRole.ADMIN, is_active=True, is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def ensure_project(db: AsyncSession, user: User) -> ProcurementProject:
    res = await db.execute(select(ProcurementProject).where(ProcurementProject.name == "Enterprise Cloud Platform Procurement"))
    p = res.scalar_one_or_none()
    if p:
        return p
    p = ProcurementProject(
        name="Enterprise Cloud Platform Procurement",
        description="Sample project used by the demo seeder.",
        category="Cloud Infrastructure", budget=500000, currency="USD",
        deadline=datetime.utcnow(), status=ProjectStatus.EVALUATION,
        created_by_id=user.id,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def ensure_vendors(db: AsyncSession) -> list[Vendor]:
    out = []
    for name, contact, email, industry in VENDORS:
        res = await db.execute(select(Vendor).where(Vendor.company_name == name))
        v = res.scalar_one_or_none()
        if not v:
            v = Vendor(company_name=name, contact_name=contact, email=email, industry=industry,
                       description=f"{name} sample vendor.", status=VendorStatus.INVITED)
            db.add(v)
            await db.commit()
            await db.refresh(v)
        out.append(v)
    return out
