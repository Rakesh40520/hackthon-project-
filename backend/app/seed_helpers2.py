"""Seed helpers part 2: requirements, project-vendors, proposals."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ProcurementProject,
    ProjectVendor,
    Proposal,
    ProposalStatus,
    ProposalDocument,
    Requirement,
    Vendor,
    VendorStatus,
)


async def ensure_requirements(db: AsyncSession, project: ProcurementProject) -> list[Requirement]:
    from app.seed_helpers import SAMPLE_REQS
    out = []
    for i, (name, desc, cat, prio, mand) in enumerate(SAMPLE_REQS):
        res = await db.execute(
            select(Requirement).where(Requirement.project_id == project.id, Requirement.name == name)
        )
        r = res.scalar_one_or_none()
        if not r:
            r = Requirement(
                project_id=project.id, name=name, description=desc,
                category=cat, priority=prio, mandatory=mand, order_index=i,
            )
            db.add(r)
            await db.commit()
            await db.refresh(r)
        out.append(r)
    return out


async def ensure_project_vendors(db: AsyncSession, project: ProcurementProject, vendors: list[Vendor]) -> list[ProjectVendor]:
    out = []
    for v in vendors:
        res = await db.execute(
            select(ProjectVendor).where(
                ProjectVendor.project_id == project.id,
                ProjectVendor.vendor_id == v.id,
            )
        )
        pv = res.scalar_one_or_none()
        if not pv:
            pv = ProjectVendor(project_id=project.id, vendor_id=v.id, status=VendorStatus.SUBMITTED)
            db.add(pv)
            await db.commit()
            await db.refresh(pv)
        out.append(pv)
    return out


async def ensure_proposals(db: AsyncSession, project_vendors: list[ProjectVendor], sample_dir: Path) -> list[Proposal]:
    from app.utils.storage import get_storage
    out = []
    storage = get_storage()
    for pv in project_vendors:
        first = pv.vendor.company_name.split()[0].lower()
        candidates = [sample_dir / f"{first}_proposal.txt", sample_dir / f"{first}_proposal.pdf", sample_dir / f"{first}_proposal.docx"]
        sample_file = next((c for c in candidates if c.exists()), None)
        if not sample_file:
            continue
        res = await db.execute(select(Proposal).where(Proposal.project_vendor_id == pv.id))
        if res.scalar_one_or_none():
            continue
        proposal = Proposal(
            project_id=pv.project_id, vendor_id=pv.vendor_id, project_vendor_id=pv.id,
            title=f"{pv.vendor.company_name} Proposal", status=ProposalStatus.UPLOADED, progress=0,
        )
        db.add(proposal)
        await db.flush()
        with open(sample_file, "rb") as f:
            data = f.read()
        path, size = storage.save_bytes(str(pv.project_id), str(pv.vendor_id), sample_file.name, data)
        doc = ProposalDocument(
            proposal_id=proposal.id, filename=sample_file.name, storage_path=path, file_size=size,
            mime_type="text/plain", file_extension=sample_file.suffix.lower(),
        )
        db.add(doc)
        await db.commit()
        await db.refresh(proposal)
        out.append(proposal)
    return out
