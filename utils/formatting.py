"""Display formatting helpers for ClauseGuard."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from core.schemas import (
    FIELD_SPECS,
    TCOStatus,
    VerificationStatus,
    coerce_decimal,
)


def format_money(value: Any) -> str:
    """Format a Decimal-ish value as USD text. Returns '—' when unparsable."""
    d: Optional[Decimal] = coerce_decimal(value)
    if d is None:
        return "—"
    if d < 0:
        return f"-${abs(d):,.2f}"
    return f"${d:,.2f}"


def format_confidence(value: Any) -> str:
    """Neutral text rendering of model confidence (never colored/styled)."""
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "—"


VERIFICATION_LABELS = {
    VerificationStatus.VERIFIED: "✓ Verified",
    VerificationStatus.UNVERIFIED: "⚠ Unverified",
    VerificationStatus.NO_EVIDENCE: "— No evidence",
}

VERIFICATION_ICONS = {
    VerificationStatus.VERIFIED: "✓",
    VerificationStatus.UNVERIFIED: "⚠",
    VerificationStatus.NO_EVIDENCE: "—",
}

TCO_STATUS_LABELS = {
    TCOStatus.MATCH: "✓ Match",
    TCOStatus.DISAGREEMENT: "⚠ Disagreement",
    TCOStatus.INSUFFICIENT_DATA: "• Insufficient data",
    TCOStatus.AI_TCO_NOT_PROVIDED: "• AI total not provided",
}


def field_label(field_name: str) -> str:
    """Human label for a field, falling back to the raw name."""
    return FIELD_SPECS.get(field_name, {}).get("label", field_name)


def field_group(field_name: str) -> str:
    return FIELD_SPECS.get(field_name, {}).get("group", "metadata")
