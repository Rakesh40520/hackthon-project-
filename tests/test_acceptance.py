"""ClauseGuard acceptance tests — runnable standalone or with pytest.

Covers the seven acceptance criteria from the product spec:

  1. A real evidence quote present in the contract returns VERIFIED.
  2. An evidence quote not present in the contract returns UNVERIFIED.
  3. High LLM confidence cannot change UNVERIFIED to VERIFIED.
  4. $10,000 setup + $2,000/month × 12 correctly calculates to $34,000.
  5. An AI-reported $50,000 TCO versus calculated $34,000 produces DISAGREEMENT.
  6. Ambiguous pricing produces INSUFFICIENT_DATA / no fabricated numbers.
  7. End-to-end demo flow (upload -> extraction -> verification -> TCO) works
     with no database or manual setup.

Run:  python tests/test_acceptance.py     (or: pytest tests/test_acceptance.py)
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.schemas import TCOStatus, VerificationStatus
from core.tco_calculator import calculate_tco
from core.verifier import normalize, verify
from services.demo_fixture import build_demo_extraction
from services.document_parser import parse_document_bytes
from services.number_parser import (
    derive_pricing_inputs,
    parse_money,
    parse_term_months,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "sample_data" / "sample_contract.txt"


def _sample_text() -> str:
    doc = parse_document_bytes(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes())
    assert doc.ok, f"Sample contract failed to parse: {doc.error}"
    return doc.text


def _real_quote() -> str:
    return (
        "This Agreement shall automatically renew for successive one-year periods "
        "unless either party provides written notice of non-renewal at least sixty "
        "(60) days before the end of the then-current term."
    )


def _fake_quote() -> str:
    return (
        "Either party may terminate this Agreement for convenience upon ninety (90) "
        "days' prior written notice to the other party."
    )


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 1
# ---------------------------------------------------------------------------

def test_acceptance_1_real_quote_is_verified() -> None:
    result = verify(_real_quote(), _sample_text())
    assert result.status is VerificationStatus.VERIFIED, result.message
    assert result.match_found is True
    assert result.message == "Evidence was found in the uploaded contract."
    # Context around the evidence should be available for the UI.
    assert result.context and "automatically renew" in result.context


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 2
# ---------------------------------------------------------------------------

def test_acceptance_2_fake_quote_is_unverified() -> None:
    result = verify(_fake_quote(), _sample_text())
    assert result.status is VerificationStatus.UNVERIFIED, result.message
    assert result.match_found is False
    assert "could not be found verbatim" in result.message


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 3
# ---------------------------------------------------------------------------

def test_acceptance_3_confidence_cannot_upgrade_unverified() -> None:
    """verify() takes no confidence input; a 0.97-confident fabricated claim
    attached to a field must still come back UNVERIFIED."""
    extraction = build_demo_extraction()
    field = extraction.get("termination_notice")
    assert field is not None and field.confidence == 0.97  # fixture is high-confidence

    result = verify(field.evidence_quote, _sample_text())
    assert result.status is VerificationStatus.UNVERIFIED
    assert result.status is not VerificationStatus.VERIFIED

    # And explicitly: even at the theoretical maximum confidence, no upgrade.
    still = verify(_fake_quote(), _sample_text())
    assert still.status is VerificationStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 4
# ---------------------------------------------------------------------------

def test_acceptance_4_tco_arithmetic_is_correct() -> None:
    result = calculate_tco(
        setup_fee=Decimal("10000"),
        recurring_fee=Decimal("2000"),
        frequency="monthly",
        term_months=12,
    )
    assert result.status is TCOStatus.AI_TCO_NOT_PROVIDED  # no AI total supplied
    assert result.calculated_total == Decimal("34000.00")
    assert any("$2,000.00 × 12 month(s) = $24,000.00" in s for s in result.calculation_steps)
    assert any("$10,000.00" in s for s in result.calculation_steps)
    assert any("Total contract cost: $34,000.00" in s for s in result.calculation_steps)


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 5
# ---------------------------------------------------------------------------

def test_acceptance_5_tco_disagreement_is_flagged() -> None:
    result = calculate_tco(
        setup_fee=Decimal("10000"),
        recurring_fee=Decimal("2000"),
        frequency="monthly",
        term_months=12,
        ai_reported_total=Decimal("50000"),
    )
    assert result.status is TCOStatus.DISAGREEMENT
    assert result.calculated_total == Decimal("34000.00")
    assert result.difference == Decimal("16000.00")
    assert "disagreement" in result.message.lower()


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 6
# ---------------------------------------------------------------------------

def test_acceptance_6_ambiguous_pricing_never_fabricates() -> None:
    # a) Ambiguous phrase -> no number, explicit warning.
    parsed = parse_money("Pricing to be mutually agreed")
    assert parsed.value is None
    assert parsed.ambiguous is True
    assert parsed.warning

    # b) Range -> no single number picked.
    ranged = parse_money("Between $10,000 and $20,000 per month")
    assert ranged.value is None
    assert ranged.ambiguous is True

    # c) Missing recurring fee -> INSUFFICIENT_DATA, not a guess.
    result = calculate_tco(setup_fee=Decimal("10000"), frequency="monthly", term_months=12)
    assert result.status is TCOStatus.INSUFFICIENT_DATA
    assert result.calculated_total is None

    # d) Missing term -> INSUFFICIENT_DATA.
    result2 = calculate_tco(recurring_fee=Decimal("2000"), frequency="monthly")
    assert result2.status is TCOStatus.INSUFFICIENT_DATA

    # e) Unparsable term text -> warning, no invented number.
    months, warning = parse_term_months("Standard enterprise term applies")
    assert months is None
    assert warning


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST 7 (end-to-end demo pipeline, no DB / no API key required)
# ---------------------------------------------------------------------------

def test_acceptance_7_end_to_end_demo_pipeline() -> None:
    doc = parse_document_bytes(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes())
    assert doc.ok
    assert doc.char_count > 1000
    assert doc.file_type == "TXT"

    extraction = build_demo_extraction()  # simulated unreliable extraction
    verifications = {
        f.field_name: verify(f.evidence_quote, doc.text)
        for f in extraction.all_fields()
    }
    pricing = derive_pricing_inputs(extraction)
    tco = calculate_tco(
        **pricing.calculator_args, ai_reported_total=pricing.ai_reported_total
    )

    # The fabricated 90-day termination claim is caught.
    assert verifications["termination_notice"].status is VerificationStatus.UNVERIFIED
    # The missing-evidence field is labeled NO_EVIDENCE.
    assert verifications["discount"].status is VerificationStatus.NO_EVIDENCE
    # Genuine claims verify.
    assert verifications["renewal_terms"].status is VerificationStatus.VERIFIED
    assert verifications["setup_fee"].status is VerificationStatus.VERIFIED
    assert verifications["recurring_fee"].status is VerificationStatus.VERIFIED

    # Deterministic TCO: 10,000 + 2,000 × 12 = 34,000 → AI's $50,000 flagged.
    assert tco.status is TCOStatus.DISAGREEMENT
    assert tco.calculated_total == Decimal("34000.00")
    assert pricing.ai_reported_total == Decimal("50000.00")
    assert tco.difference == Decimal("16000.00")
    # Unit-priced usage is excluded, never guessed into the total.
    assert pricing.usage_cost is None


# ---------------------------------------------------------------------------
# Bonus robustness checks for the deterministic layer
# ---------------------------------------------------------------------------

def test_extra_normalization_handles_variants() -> None:
    source = "Fees are \u201cnon\u2013refundable\u201d\u00a0under\u00a0this\u00a0Agreement."
    quote = 'Fees are "non-refundable" under this Agreement.'
    assert normalize(source) == normalize(quote)
    assert verify(quote, source).status is VerificationStatus.VERIFIED


def test_extra_money_formats_parse() -> None:
    assert parse_money("$10,000").value == Decimal("10000")
    assert parse_money("USD 10,000").value == Decimal("10000")
    assert parse_money("$2,500/month").value == Decimal("2500")
    assert parse_money("$2,500/month").frequency_hint == "monthly"
    assert parse_money("$30,000 per year").frequency_hint == "annual"


def test_extra_empty_and_null_evidence() -> None:
    assert verify(None, "some source").status is VerificationStatus.NO_EVIDENCE
    assert verify("   ", "some source").status is VerificationStatus.NO_EVIDENCE
    assert verify("quote", "").status is VerificationStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# Standalone runner (also pytest-compatible)
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        ("Acceptance 1: real quote -> VERIFIED", test_acceptance_1_real_quote_is_verified),
        ("Acceptance 2: fake quote -> UNVERIFIED", test_acceptance_2_fake_quote_is_unverified),
        ("Acceptance 3: confidence cannot upgrade", test_acceptance_3_confidence_cannot_upgrade_unverified),
        ("Acceptance 4: 10k + 2k×12 = 34,000", test_acceptance_4_tco_arithmetic_is_correct),
        ("Acceptance 5: $50k vs $34k -> DISAGREEMENT", test_acceptance_5_tco_disagreement_is_flagged),
        ("Acceptance 6: ambiguous pricing -> no fabrication", test_acceptance_6_ambiguous_pricing_never_fabricates),
        ("Acceptance 7: end-to-end demo pipeline", test_acceptance_7_end_to_end_demo_pipeline),
        ("Extra: normalization variants", test_extra_normalization_handles_variants),
        ("Extra: money formats", test_extra_money_formats_parse),
        ("Extra: empty/null evidence", test_extra_empty_and_null_evidence),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())


