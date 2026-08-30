"""Scoring and mandatory-requirement tests."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import (
    EvaluationStatus,
    ProcurementProject,
    ProjectStatus,
    ProjectVendor,
    Proposal,
    ProposalStatus,
    Requirement,
    RequirementCategory,
    RequirementEvaluation,
    RequirementPriority,
    User,
    UserRole,
    Vendor,
    VendorStatus,
)


@pytest.mark.asyncio
async def test_mandatory_failure_makes_ineligible(db_session):
    # Seed
    user = User(name="u", email="u@x.com", hashed_password="x", role=UserRole.ADMIN, is_active=True)
    db_session.add(user)
    await db_session.flush()
    project = ProcurementProject(
        name="p", created_by_id=user.id, status=ProjectStatus.EVALUATION,
    )
    db_session.add(project)
    await db_session.flush()
    v = Vendor(company_name="V", status=VendorStatus.INVITED)
    db_session.add(v)
    await db_session.flush()
    pv = ProjectVendor(project_id=project.id, vendor_id=v.id, status=VendorStatus.SUBMITTED)
    db_session.add(pv)
    await db_session.flush()
    p = Proposal(project_id=project.id, vendor_id=v.id, project_vendor_id=pv.id, title="t", status=ProposalStatus.UPLOADED)
    db_session.add(p)
    await db_session.flush()
    req = Requirement(
        project_id=project.id, name="Must support SAML", category=RequirementCategory.SECURITY,
        priority=RequirementPriority.CRITICAL, mandatory=True,
    )
    db_session.add(req)
    await db_session.flush()
    ev = RequirementEvaluation(
        proposal_id=p.id, requirement_id=req.id,
        status=EvaluationStatus.DOES_NOT_MEET, score=10, reason="missing", confidence=0.9,
    )
    db_session.add(ev)
    await db_session.commit()

    from app.services.scoring_service import compute_vendor_score, _check_mandatory_failures
    fails = await _check_mandatory_failures(db_session, p)
    assert any("SAML" in f for f in fails)
    score = await compute_vendor_score(db_session, p, project)
    assert score.is_eligible is False
    assert score.ineligibility_reasons


@pytest.mark.asyncio
async def test_weights_normalized_in_total(db_session):
    user = User(name="u", email="u2@x.com", hashed_password="x", role=UserRole.ADMIN, is_active=True)
    db_session.add(user)
    await db_session.flush()
    project = ProcurementProject(
        name="p2", created_by_id=user.id, status=ProjectStatus.EVALUATION,
        weight_price=0.5, weight_technical=0.5, weight_security=0.0,
        weight_support=0.0, weight_implementation=0.0, weight_contract=0.0,
    )
    db_session.add(project)
    await db_session.flush()
    v = Vendor(company_name="V2", status=VendorStatus.INVITED)
    db_session.add(v)
    await db_session.flush()
    pv = ProjectVendor(project_id=project.id, vendor_id=v.id, status=VendorStatus.SUBMITTED)
    db_session.add(pv)
    await db_session.flush()
    p = Proposal(project_id=project.id, vendor_id=v.id, project_vendor_id=pv.id, title="t", status=ProposalStatus.UPLOADED)
    db_session.add(p)
    await db_session.flush()
    req = Requirement(
        project_id=project.id, name="REST API", category=RequirementCategory.TECHNICAL,
        priority=RequirementPriority.HIGH, mandatory=True,
    )
    db_session.add(req)
    await db_session.flush()
    ev = RequirementEvaluation(
        proposal_id=p.id, requirement_id=req.id, status=EvaluationStatus.MEETS, score=100, reason="ok", confidence=0.95,
    )
    db_session.add(ev)
    await db_session.commit()

    from app.services.scoring_service import compute_vendor_score
    score = await compute_vendor_score(db_session, p, project)
    # With only technical evaluated, the total should be close to 100 (since 0.5 weight on 100).
    assert 80 <= score.total_score <= 100
    assert score.is_eligible
