"""Vendor info, pricing, technical extraction steps."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import (
    PricingAnalysis,
    TechnicalCapabilities,
    VendorInformation,
    get_ai_provider,
)
from app.ai.provider import ChatMessage
from app.models import (
    ExtractedField,
    PricingDetail,
    Proposal,
)
from app.services.extraction_service import _chunk_text


async def extract_vendor_info(db: AsyncSession, proposal: Proposal, text: str) -> VendorInformation:
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Extract the vendor information from this proposal. Use null if not present. "
            "Do not fabricate. Return evidence with quote if possible.\n\n" + _chunk_text(text)
        ))
    ]
    res: VendorInformation = await ai.complete(messages=msgs, response_model=VendorInformation)
    for f in (res.fields or []):
        ef = ExtractedField(
            proposal_id=proposal.id, field_name=f.field_name, field_group="vendor",
            value=f.value, value_type="string", confidence=f.confidence,
            is_fact=f.is_fact, is_inferred=f.is_inferred,
            source_document=f.evidence.document, source_page=f.evidence.page,
            source_section=f.evidence.section, source_quote=f.evidence.quote,
        )
        db.add(ef)
    if res.vendor_name and (not proposal.title or proposal.title == "Untitled Proposal"):
        proposal.title = f"{res.vendor_name} Proposal"
    if res.proposal_date:
        try:
            proposal.proposal_date = datetime.fromisoformat(res.proposal_date)
        except Exception:
            pass
    if res.valid_until:
        try:
            proposal.valid_until = datetime.fromisoformat(res.valid_until)
        except Exception:
            pass
    await db.commit()
    return res


async def extract_pricing(db: AsyncSession, proposal: Proposal, text: str) -> PricingAnalysis:
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Extract pricing information from this proposal. "
            "Return null for any value not explicitly stated. Include currency. "
            "Do not invent numbers. Show all assumptions.\n\n" + _chunk_text(text)
        ))
    ]
    res: PricingAnalysis = await ai.complete(messages=msgs, response_model=PricingAnalysis)

    pd = proposal.pricing
    if pd is None:
        pd = PricingDetail(proposal_id=proposal.id)
        db.add(pd)
    for fld in [
        "currency", "total_cost", "annual_cost", "monthly_cost", "implementation_cost",
        "license_cost", "support_cost", "maintenance_cost", "training_cost", "migration_cost",
        "additional_fees", "discounts", "taxes", "year1_total", "year3_total", "year5_total",
        "recurring_annual_cost", "pricing_model", "billing_frequency", "price_escalation_pct",
    ]:
        if getattr(res, fld, None) is not None:
            setattr(pd, fld, getattr(res, fld))
    pd.assumptions = {"assumptions": res.assumptions, "notes": res.notes}
    pd.raw_breakdown = res.model_dump()
    for f in (res.fields or []):
        ef = ExtractedField(
            proposal_id=proposal.id, field_name=f.field_name, field_group="pricing",
            value=f.value, value_type="number", confidence=f.confidence,
            is_fact=f.is_fact, is_inferred=f.is_inferred,
            source_document=f.evidence.document, source_page=f.evidence.page,
            source_section=f.evidence.section, source_quote=f.evidence.quote,
        )
        db.add(ef)
    await db.commit()
    return res


async def extract_technical(db: AsyncSession, proposal: Proposal, text: str) -> TechnicalCapabilities:
    ai = get_ai_provider()
    msgs = [
        ChatMessage(role="user", content=(
            "Extract technical capabilities. Return true/false only when the proposal explicitly "
            "states the capability. Use null if not mentioned. Never invent features.\n\n" + _chunk_text(text)
        ))
    ]
    res: TechnicalCapabilities = await ai.complete(messages=msgs, response_model=TechnicalCapabilities)
    fields_map = {
        "api": res.api, "api_rest": res.api_rest, "api_graphql": res.api_graphql,
        "api_soap": res.api_soap, "sso": res.sso, "oauth": res.oauth, "saml": res.saml,
        "encryption_at_rest": res.encryption_at_rest,
        "encryption_in_transit": res.encryption_in_transit,
        "cloud_deployment": res.cloud_deployment,
        "on_premise_deployment": res.on_premise_deployment,
        "sla_percentage": res.sla_percentage, "max_concurrent_users": res.max_concurrent_users,
        "backup": res.backup, "disaster_recovery": res.disaster_recovery,
        "monitoring": res.monitoring,
    }
    for name, val in fields_map.items():
        if val is None:
            continue
        ef = ExtractedField(
            proposal_id=proposal.id, field_name=name, field_group="technical",
            value=str(val), value_type="bool" if isinstance(val, bool) else "number",
            confidence=0.85,
        )
        db.add(ef)
    for it in (res.integrations or []):
        ef = ExtractedField(proposal_id=proposal.id, field_name="integration", field_group="technical", value=it, value_type="string", confidence=0.8)
        db.add(ef)
    for c in (res.compliance or []):
        ef = ExtractedField(proposal_id=proposal.id, field_name="compliance", field_group="technical", value=c, value_type="string", confidence=0.8)
        db.add(ef)
    for d in (res.database_support or []):
        ef = ExtractedField(proposal_id=proposal.id, field_name="database_support", field_group="technical", value=d, value_type="string", confidence=0.8)
        db.add(ef)
    await db.commit()
    return res
