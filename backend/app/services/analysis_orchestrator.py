"""End-to-end analysis pipeline orchestration."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import RecommendationResult, get_ai_provider
from app.ai.provider import ChatMessage
from app.models import (
    EvaluationStatus,
    JobStage,
    JobStatus,
    ProcurementProject,
    ProjectVendor,
    Proposal,
    ProposalStatus,
    Recommendation,
    RequirementEvaluation,
    Risk,
    RiskSeverity,
    VendorScore,
)
from app.services.evaluation_steps import evaluate_requirements
from app.services.extraction_service import run_extraction
from app.services.extraction_steps import extract_pricing, extract_technical, extract_vendor_info
from app.services.job_service import get_or_create_job, update_job
from app.services.risk_steps import analyze_risks, detect_missing, generate_clarifications
from app.services.scoring_service import assign_ranks, compute_vendor_score

logger = logging.getLogger(__name__)


async def run_full_analysis(db: AsyncSession, proposal_id: str) -> None:
    job = await get_or_create_job(db, proposal_id)
    try:
        await update_job(db, job, status=JobStatus.RUNNING, started=True, message="Starting analysis")

        prop_res = await db.execute(
            select(Proposal)
            .options(
                selectinload(Proposal.project_vendor).selectinload(ProjectVendor.vendor),
                selectinload(Proposal.documents),
            )
            .where(Proposal.id == proposal_id)
        )
        proposal = prop_res.scalar_one()
        proposal.status = ProposalStatus.PROCESSING
        await db.commit()

        await update_job(db, job, stage=JobStage.EXTRACT, progress=5, message="Extracting documents")
        text = await run_extraction(db, proposal)
        if not text.strip():
            raise ValueError("No extractable text in proposal documents")
        await update_job(db, job, progress=15, message=f"Extracted {len(text)} characters")

        await update_job(db, job, stage=JobStage.ANALYZE, progress=20, message="Extracting vendor information")
        await extract_vendor_info(db, proposal, text)
        await update_job(db, job, progress=30, message="Vendor info extracted")

        await update_job(db, job, progress=35, message="Analyzing pricing")
        await extract_pricing(db, proposal, text)
        await update_job(db, job, progress=45, message="Pricing normalized")

        await update_job(db, job, progress=50, message="Extracting technical capabilities")
        await extract_technical(db, proposal, text)
        await update_job(db, job, progress=58, message="Capabilities extracted")

        proj_res = await db.execute(
            select(ProcurementProject).where(ProcurementProject.id == proposal.project_id)
        )
        project = proj_res.scalar_one()
        await update_job(db, job, stage=JobStage.EVALUATE_REQUIREMENTS, progress=62, message="Evaluating requirements")
        await evaluate_requirements(db, proposal, project, text)
        await update_job(db, job, progress=70, message="Requirements evaluated")

        await update_job(db, job, stage=JobStage.ANALYZE_RISKS, progress=75, message="Detecting risks")
        await analyze_risks(db, proposal, text)
        await update_job(db, job, progress=82, message="Risks detected")

        await update_job(db, job, progress=85, message="Identifying missing information")
        await detect_missing(db, proposal, text)
        await update_job(db, job, progress=88, message="Missing info identified")

        await update_job(db, job, progress=90, message="Generating clarifications")
        await generate_clarifications(db, proposal)
        await update_job(db, job, progress=92, message="Clarifications generated")

        await update_job(db, job, stage=JobStage.SCORE, progress=94, message="Computing scores")
        score = await compute_vendor_score(db, proposal, project)
        await update_job(db, job, progress=96, message="Scores computed")

        await update_job(db, job, stage=JobStage.RECOMMEND, progress=98, message="Generating recommendation")
        await generate_recommendation(db, proposal, project, score)
        await update_job(db, job, progress=100, message="Analysis complete")

        proposal.status = ProposalStatus.COMPLETED
        proposal.progress = 100
        proposal.analyzed_at = datetime.now(timezone.utc)
        await db.commit()

        await assign_ranks(db, str(project.id))
        await update_job(db, job, status=JobStatus.COMPLETED, completed=True, message="Completed")
    except Exception as e:
        logger.exception("Analysis failed for proposal %s", proposal_id)
        try:
            prop_res = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
            p = prop_res.scalar_one_or_none()
            if p:
                p.status = ProposalStatus.FAILED
                p.error_message = str(e)
                await db.commit()
        except Exception:
            pass
        await update_job(db, job, status=JobStatus.FAILED, error=str(e), completed=True)

async def generate_recommendation(
    db: AsyncSession, proposal: Proposal, project: ProcurementProject, score: VendorScore
) -> Recommendation:
    evals_res = await db.execute(
        select(RequirementEvaluation)
        .options(selectinload(RequirementEvaluation.requirement))
        .where(RequirementEvaluation.proposal_id == proposal.id)
    )
    evals = evals_res.scalars().all()
    meets = sum(1 for e in evals if e.status == EvaluationStatus.MEETS)
    partial = sum(1 for e in evals if e.status == EvaluationStatus.PARTIALLY_MEETS)
    fails = sum(1 for e in evals if e.status == EvaluationStatus.DOES_NOT_MEET)
    mandatory_fails = [
        e.requirement.name for e in evals
        if e.requirement.mandatory and e.status in (EvaluationStatus.DOES_NOT_MEET, EvaluationStatus.UNKNOWN)
    ]

    risks_res = await db.execute(select(Risk).where(Risk.proposal_id == proposal.id))
    risks = risks_res.scalars().all()
    high_risks = [r for r in risks if r.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL)]

    strengths = [
        f"Meets {meets} requirements" if meets else None,
        "Strong pricing" if (proposal.pricing and (proposal.pricing.year1_total or 0) < 200000) else None,
        f"Low risk profile ({len(risks)} risks)" if len(risks) <= 2 else None,
    ]
    weaknesses = [
        f"Missing {fails} requirements" if fails else None,
        f"{len(high_risks)} high-severity risks" if high_risks else None,
        "Pricing unavailable" if not (proposal.pricing and proposal.pricing.year1_total) else None,
    ]
    strengths = [s for s in strengths if s] or ["Meets core requirements"]
    weaknesses = [w for w in weaknesses if w] or ["No major weaknesses detected"]

    ctx = {
        "score": score.total_score, "eligible": score.is_eligible, "rank": score.rank,
        "meets": meets, "partial": partial, "fails": fails,
        "mandatory_fails": mandatory_fails, "risks_total": len(risks),
        "high_risks": [r.title for r in high_risks], "strengths": strengths, "weaknesses": weaknesses,
    }
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Write a structured recommendation for this vendor based on the objective context. "
            "Use the deterministic score and reasons; do not invent metrics. Be concise and professional.\n\n"
            f"RECO_CONTEXT: {json.dumps(ctx)}\n\n"
            "Return: recommended (bool), rank, summary, reasoning, strengths (list), weaknesses (list), "
            "next_steps (list), decision (RECOMMENDED|ACCEPTABLE_WITH_CAVEATS|INELIGIBLE)."
        ))
    ]
    res: RecommendationResult = await ai.complete(messages=msgs, response_model=RecommendationResult)

    rec = proposal.recommendation
    if rec is None:
        rec = Recommendation(proposal_id=proposal.id)
        db.add(rec)
    rec.recommended = res.recommended
    rec.rank = res.rank
    rec.summary = res.summary
    rec.reasoning = res.reasoning
    rec.strengths = res.strengths
    rec.weaknesses = res.weaknesses
    rec.next_steps = res.next_steps
    rec.decision = res.decision
    await db.commit()
    return rec
