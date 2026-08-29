"""Independent, deterministic Total Cost of Ownership calculator.

This module contains ZERO language-model logic. It takes structured numeric
inputs (already parsed conservatively by services.number_parser) and performs
exact Decimal arithmetic. The AI's reported TCO is compared against this
independently computed total — never the other way around.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from core.schemas import TCOStatus, TCOResult, coerce_decimal
from utils.formatting import format_money

_CENTS = Decimal("0.01")
DEFAULT_ROUNDING_TOLERANCE = Decimal("0.01")

SUPPORTED_FREQUENCIES = ("monthly", "quarterly", "annual")


def _q(value: Decimal) -> Decimal:
    """Quantize to cents (half-up)."""
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def calculate_tco(
    setup_fee: Any = None,
    recurring_fee: Any = None,
    frequency: Any = None,
    term_months: Any = None,
    minimum_commitment: Any = None,
    usage_cost: Any = None,
    ai_reported_total: Any = None,
    rounding_tolerance: Decimal = DEFAULT_ROUNDING_TOLERANCE,
) -> TCOResult:
    """Compute the contract total deterministically and compare it to the AI's claim.

    Returns a TCOResult whose status is one of:
      - MATCH:            AI-reported total agrees with deterministic arithmetic
                          (within `rounding_tolerance`).
      - DISAGREEMENT:     AI-reported total differs materially from the arithmetic.
      - INSUFFICIENT_DATA: not enough structured inputs; nothing was fabricated.
      - AI_TCO_NOT_PROVIDED: calculation succeeded but the model reported no total.
    """
    setup = coerce_decimal(setup_fee)
    recurring = coerce_decimal(recurring_fee)
    minimum = coerce_decimal(minimum_commitment)
    usage = coerce_decimal(usage_cost)
    ai_total = coerce_decimal(ai_reported_total)

    freq = str(frequency).strip().lower() if frequency else None
    term: Optional[int] = None
    if term_months is not None:
        try:
            term = int(term_months)
        except (TypeError, ValueError):
            term_dec = coerce_decimal(term_months)
            term = int(term_dec) if term_dec is not None else None

    steps: list = []
    warnings: list = []

    # ---- Insufficient data guard -------------------------------------------
    missing: list = []
    if term is None or term <= 0:
        missing.append("contract term in months")
    if recurring is None:
        missing.append("recurring fee amount")
    elif freq not in SUPPORTED_FREQUENCIES:
        missing.append("a supported billing frequency (monthly, quarterly, or annual)")

    if missing:
        steps.append("Deterministic calculation could not be performed.")
        for item in missing:
            steps.append(f"  • Missing: {item}.")
        steps.append(
            "ClauseGuard refuses to guess missing inputs — no arithmetic was fabricated."
        )
        return TCOResult(
            status=TCOStatus.INSUFFICIENT_DATA,
            setup_fee=setup,
            recurring_fee=recurring,
            frequency=freq,
            term_months=term if term is not None and term > 0 else None,
            minimum_commitment=minimum,
            usage_cost=usage,
            ai_reported_total=ai_total,
            calculation_steps=steps,
            warnings=warnings,
            message=(
                "Not enough structured pricing information for a reliable "
                "calculation (missing: " + ", ".join(missing) + ")."
            ),
        )

    term_dec = Decimal(term)

    # ---- Setup fee ----------------------------------------------------------
    setup_value = setup if setup is not None else Decimal("0")
    steps.append(f"Setup fee: {format_money(setup_value)}")

    # ---- Recurring fee ------------------------------------------------------
    if freq == "monthly":
        recurring_total = _q(recurring * term_dec)
        steps.append(
            f"Recurring fee: {format_money(recurring)} × {term} month(s) = {format_money(recurring_total)}"
        )
    elif freq == "annual":
        recurring_total = _q(recurring * term_dec / Decimal("12"))
        steps.append(
            f"Annual fee: {format_money(recurring)} × {term}/12 = {format_money(recurring_total)}"
        )
        if term % 12 != 0:
            warnings.append(
                "Contract term is not a whole number of years; the annual fee was prorated."
            )
    else:  # quarterly
        recurring_total = _q(recurring * term_dec / Decimal("3"))
        steps.append(
            f"Quarterly fee: {format_money(recurring)} × {term}/3 = {format_money(recurring_total)}"
        )
        if term % 3 != 0:
            warnings.append(
                "Contract term is not a whole number of quarters; the quarterly fee was prorated."
            )

    # ---- Explicit usage cost (only when a flat amount was stated) -----------
    usage_value = usage if usage is not None else Decimal("0")
    if usage is not None:
        steps.append(f"Explicit usage cost: {format_money(usage_value)}")

    # ---- Subtotal ------------------------------------------------------------
    subtotal = setup_value + recurring_total + usage_value
    total = subtotal

    # ---- Minimum commitment (always a total-over-term figure by the time it
    #      reaches this function; number_parser handles conversions) ----------
    if minimum is not None:
        steps.append(f"Minimum commitment (over full term): {format_money(minimum)}")
        if subtotal < minimum:
            total = minimum
            warnings.append(
                "Calculated costs are below the stated minimum commitment; "
                "the total was raised to the minimum."
            )
            steps.append(
                f"Minimum commitment applies: total raised from "
                f"{format_money(subtotal)} to {format_money(minimum)}."
            )
        else:
            steps.append("Minimum commitment check: satisfied — it does not change the total.")

    calculated_total = _q(total)
    steps.append(f"Total contract cost: {format_money(calculated_total)}")

    # ---- Comparison with the AI's reported total -----------------------------
    if ai_total is not None:
        difference = ai_total - calculated_total
        if abs(difference) <= rounding_tolerance:
            status = TCOStatus.MATCH
            message = (
                f"AI-reported TCO ({format_money(ai_total)}) matches the "
                f"deterministic calculation ({format_money(calculated_total)})."
            )
        else:
            status = TCOStatus.DISAGREEMENT
            message = (
                f"Arithmetic disagreement: the AI reported {format_money(ai_total)} "
                f"but the extracted pricing terms deterministically total "
                f"{format_money(calculated_total)} (difference {format_money(difference)})."
            )
        steps.append(
            f"AI-reported total: {format_money(ai_total)} — "
            f"difference vs deterministic total: {format_money(difference)}"
        )
    else:
        difference = None
        status = TCOStatus.AI_TCO_NOT_PROVIDED
        message = (
            "The AI extraction did not report a total cost. The deterministic "
            "calculation is shown for reference."
        )

    return TCOResult(
        status=status,
        setup_fee=setup,
        recurring_fee=recurring,
        frequency=freq,
        term_months=term,
        minimum_commitment=minimum,
        usage_cost=usage,
        calculated_total=calculated_total,
        ai_reported_total=ai_total,
        difference=difference,
        calculation_steps=steps,
        warnings=warnings,
        message=message,
    )

