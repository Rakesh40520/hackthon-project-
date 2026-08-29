"""Pydantic schemas for ClauseGuard.

All AI output passes through these models. The models are deliberately
defensive: the LLM is treated as an *untrusted extractor*, so parsing is
tolerant of malformed responses and never trusts anything the model says
about its own reliability. Verification is always performed downstream by
core.verifier (deterministic code), never by the model.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Field registry — single source of truth for extraction + UI labels
# ---------------------------------------------------------------------------

FIELD_SPECS: Dict[str, Dict[str, str]] = {
    # --- Contract metadata -------------------------------------------------
    "vendor_name": {
        "group": "metadata",
        "label": "Vendor name",
        "description": "Legal name of the vendor/supplier providing the product or service.",
    },
    "customer_name": {
        "group": "metadata",
        "label": "Customer name",
        "description": "Legal name of the customer purchasing the product or service.",
    },
    "contract_title": {
        "group": "metadata",
        "label": "Contract title",
        "description": "Official title of the agreement as stated in the document.",
    },
    "effective_date": {
        "group": "metadata",
        "label": "Effective date",
        "description": "Effective date of the agreement exactly as written in the document.",
    },
    "contract_term": {
        "group": "metadata",
        "label": "Contract term",
        "description": "Initial contract term length (e.g. '12 months', '3 years').",
    },
    "renewal_terms": {
        "group": "metadata",
        "label": "Renewal terms",
        "description": "How and when the contract renews, including non-renewal notice periods.",
    },
    # --- Commercial terms ---------------------------------------------------
    "setup_fee": {
        "group": "commercial_terms",
        "label": "Setup fee",
        "description": "One-time setup, implementation or onboarding fee, amount exactly as written.",
    },
    "recurring_fee": {
        "group": "commercial_terms",
        "label": "Recurring fee",
        "description": "Recurring subscription/license fee exactly as written (e.g. '$2,000 per month').",
    },
    "recurring_fee_frequency": {
        "group": "commercial_terms",
        "label": "Recurring fee frequency",
        "description": "Billing frequency of the recurring fee: monthly, quarterly, or annual. Null if not stated.",
    },
    "minimum_commitment": {
        "group": "commercial_terms",
        "label": "Minimum commitment",
        "description": "Any minimum spend or minimum contract value commitment, exactly as written.",
    },
    "usage_based_costs": {
        "group": "commercial_terms",
        "label": "Usage-based costs",
        "description": "Usage-based, metered or overage costs (per-query, per-GB, per-seat), exactly as written.",
    },
    "discount": {
        "group": "commercial_terms",
        "label": "Discount",
        "description": "Any discounts or promotional pricing. Null if the contract says nothing about discounts.",
    },
    "payment_terms": {
        "group": "commercial_terms",
        "label": "Payment terms",
        "description": "Invoice payment terms (e.g. 'Net 30').",
    },
    "price_increase_terms": {
        "group": "commercial_terms",
        "label": "Price increase terms",
        "description": "Allowed price increases, including caps and when they apply.",
    },
    # --- Risk & operational terms -------------------------------------------
    "termination_notice": {
        "group": "risk_terms",
        "label": "Termination notice",
        "description": "Termination rights and required notice periods, exactly as written.",
    },
    "auto_renewal": {
        "group": "risk_terms",
        "label": "Auto-renewal",
        "description": "Whether and how the contract automatically renews.",
    },
    "liability_cap": {
        "group": "risk_terms",
        "label": "Liability cap",
        "description": "Limitation of liability, including any cap and how it is calculated.",
    },
    "data_processing_terms": {
        "group": "risk_terms",
        "label": "Data processing terms",
        "description": "Data processing, security and privacy commitments.",
    },
    "governing_law": {
        "group": "risk_terms",
        "label": "Governing law",
        "description": "Governing law / jurisdiction clause.",
    },
}

GROUP_LABELS: Dict[str, str] = {
    "metadata": "Contract Metadata",
    "commercial_terms": "Commercial Terms",
    "risk_terms": "Risk & Operational Terms",
}

GROUP_ORDER = ("metadata", "commercial_terms", "risk_terms")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    NO_EVIDENCE = "NO_EVIDENCE"


class TCOStatus(str, Enum):
    MATCH = "MATCH"
    DISAGREEMENT = "DISAGREEMENT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    AI_TCO_NOT_PROVIDED = "AI_TCO_NOT_PROVIDED"


# ---------------------------------------------------------------------------
# Defensive coercion helpers
# ---------------------------------------------------------------------------

def coerce_decimal(value: Any) -> Optional[Decimal]:
    """Best-effort Decimal coercion. Returns None rather than guessing."""
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("$", "").strip()
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def _coerce_confidence(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(1.0, f)), 4)


def _to_text(value: Any) -> Optional[str]:
    """Coerce arbitrary LLM output to a clean string or None. Never invents."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, (list, tuple)):
        joined = "; ".join(str(v) for v in value if v is not None)
        return joined or None
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class EvidenceField(BaseModel):
    """One extracted contract field plus the evidence the model claims supports it."""

    field_name: str
    group: str = "metadata"
    value: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: Optional[float] = None
    source_location_hint: Optional[str] = None

    @field_validator("value", "evidence_quote", "source_location_hint", mode="before")
    @classmethod
    def _clean_text(cls, v: Any) -> Optional[str]:
        return _to_text(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def _clean_confidence(cls, v: Any) -> Optional[float]:
        return _coerce_confidence(v)

    @property
    def has_claim(self) -> bool:
        """True when the model actually asserted something for this field."""
        return bool(self.value or self.evidence_quote)


class VerificationResult(BaseModel):
    """Outcome of the deterministic verify() check (never produced by an LLM)."""

    status: VerificationStatus
    match_found: bool = False
    normalized_quote: str = ""
    message: str = ""
    context: Optional[str] = None


class TCOResult(BaseModel):
    """Outcome of the independent deterministic TCO calculation + comparison."""

    status: TCOStatus
    setup_fee: Optional[Decimal] = None
    recurring_fee: Optional[Decimal] = None
    frequency: Optional[str] = None
    term_months: Optional[int] = None
    minimum_commitment: Optional[Decimal] = None
    usage_cost: Optional[Decimal] = None
    calculated_total: Optional[Decimal] = None
    ai_reported_total: Optional[Decimal] = None
    ai_reported_raw: Optional[str] = None
    difference: Optional[Decimal] = None
    calculation_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    message: str = ""

    @field_validator(
        "setup_fee",
        "recurring_fee",
        "minimum_commitment",
        "usage_cost",
        "calculated_total",
        "ai_reported_total",
        "difference",
        mode="before",
    )
    @classmethod
    def _dec(cls, v: Any) -> Optional[Decimal]:
        return coerce_decimal(v)

    @field_validator("term_months", mode="before")
    @classmethod
    def _int(cls, v: Any) -> Optional[int]:
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            d = coerce_decimal(v)
            return int(d) if d is not None else None


class ContractExtraction(BaseModel):
    """Full extraction result: every known field plus the AI-reported TCO."""

    fields: Dict[str, EvidenceField] = Field(default_factory=dict)
    ai_reported_tco: Optional[str] = None
    raw_notes: Optional[str] = None

    @field_validator("ai_reported_tco", "raw_notes", mode="before")
    @classmethod
    def _text2(cls, v: Any) -> Optional[str]:
        return _to_text(v)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "ContractExtraction":
        """Defensively build an extraction from an arbitrary parsed JSON dict.

        Never raises on odd payloads beyond the top-level type check; unknown
        fields are recorded in raw_notes instead of crashing.
        """
        if not isinstance(raw, Mapping):
            raise ValueError("LLM JSON payload was not a JSON object.")

        unknown: List[str] = []
        fields: Dict[str, EvidenceField] = {}

        for group in GROUP_ORDER:
            block = raw.get(group)
            if not isinstance(block, Mapping):
                continue
            for name, payload in block.items():
                fname = str(name).strip()
                if fname not in FIELD_SPECS:
                    unknown.append(f"{group}.{fname}")
                    continue
                if isinstance(payload, Mapping):
                    fields[fname] = EvidenceField(
                        field_name=fname,
                        group=group,
                        value=payload.get("value"),
                        evidence_quote=payload.get("evidence_quote"),
                        confidence=payload.get("confidence"),
                        source_location_hint=payload.get("source_location_hint"),
                    )
                else:
                    # Model returned a bare value instead of the object schema.
                    fields[fname] = EvidenceField(field_name=fname, group=group, value=payload)

        # Ensure every known field exists so the UI and metrics are stable.
        for fname, spec in FIELD_SPECS.items():
            fields.setdefault(fname, EvidenceField(field_name=fname, group=spec["group"]))

        notes = raw.get("raw_notes") or raw.get("notes")
        if unknown:
            extra = "Unrecognized fields returned by the model (ignored): " + ", ".join(sorted(unknown))
            notes = f"{notes}\n{extra}" if notes else extra

        return cls(fields=fields, ai_reported_tco=raw.get("ai_reported_tco"), raw_notes=notes)

    def all_fields(self) -> List[EvidenceField]:
        """Fields in the canonical registry order."""
        return [self.fields[name] for name in FIELD_SPECS if name in self.fields]

    def get(self, name: str) -> Optional[EvidenceField]:
        return self.fields.get(name)


class DocumentInfo(BaseModel):
    file_name: str = ""
    file_type: str = ""
    char_count: int = 0
    page_count: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Everything the UI needs for one analyzed contract."""

    mode: str = "live"  # "live" (LLM) or "demo" (simulated fixture)
    created_at: str = ""
    document: DocumentInfo = Field(default_factory=DocumentInfo)
    extraction: ContractExtraction = Field(default_factory=ContractExtraction)
    verifications: Dict[str, VerificationResult] = Field(default_factory=dict)
    tco: Optional[TCOResult] = None
    pricing_rows: List[Dict[str, str]] = Field(default_factory=list)
    pricing_warnings: List[str] = Field(default_factory=list)
    source_text: str = ""

    @property
    def extracted_count(self) -> int:
        return sum(1 for f in self.extraction.all_fields() if f.value)

    def _count_status(self, status: VerificationStatus) -> int:
        return sum(
            1
            for f in self.extraction.all_fields()
            if f.field_name in self.verifications
            and self.verifications[f.field_name].status is status
        )

    @property
    def verified_count(self) -> int:
        return self._count_status(VerificationStatus.VERIFIED)

    @property
    def unverified_count(self) -> int:
        return self._count_status(VerificationStatus.UNVERIFIED)

    @property
    def no_evidence_count(self) -> int:
        return self._count_status(VerificationStatus.NO_EVIDENCE)

    def attention_fields(self) -> List[EvidenceField]:
        """Fields that belong in 'Claims Requiring Attention'.

        A field is flagged when its evidence is UNVERIFIED, or when the model
        asserted a value without supplying any evidence at all.
        """
        flagged: List[EvidenceField] = []
        for f in self.extraction.all_fields():
            v = self.verifications.get(f.field_name)
            if v is None:
                continue
            if v.status is VerificationStatus.UNVERIFIED:
                flagged.append(f)
            elif v.status is VerificationStatus.NO_EVIDENCE and f.value:
                flagged.append(f)
        return flagged

