"""Demo fixture: a SIMULATED extraction for demo mode.

This fixture is used ONLY when the user explicitly runs demo mode. It simulates
an unreliable LLM extraction against sample_data/sample_contract.txt:

  * Most evidence quotes are real (verbatim from the sample contract) and will
    verify cleanly.
  * The `termination_notice` claim is INTENTIONALLY fabricated: the quote is
    not present in the contract (the contract says 30 days, the fixture claims
    90 days) with HIGH model confidence — demonstrating that ClauseGuard catches
    unsupported claims regardless of confidence.
  * `discount` has no evidence at all — demonstrating the NO_EVIDENCE path.
  * `ai_reported_tco` is $50,000 while deterministic arithmetic yields $34,000
    — demonstrating the TCO disagreement banner.

Live extraction NEVER injects false answers; this fixture exists so the
verification layer can be demonstrated without an API key.
"""

from __future__ import annotations

from core.schemas import ContractExtraction, EvidenceField


def _f(name: str, group: str, value=None, quote=None, conf=None, hint=None) -> EvidenceField:
    return EvidenceField(
        field_name=name,
        group=group,
        value=value,
        evidence_quote=quote,
        confidence=conf,
        source_location_hint=hint,
    )


def build_demo_extraction() -> ContractExtraction:
    """Build the simulated (partially unreliable) extraction."""
    fields = [
        # --- Contract metadata (all genuine) ---------------------------------
        _f("vendor_name", "metadata",
           "CloudScope Analytics, Inc.",
           'CloudScope Analytics, Inc., a Delaware corporation ("Vendor")',
           0.95, "Preamble"),
        _f("customer_name", "metadata",
           "Meridian Retail Group, LLC",
           'Meridian Retail Group, LLC, a New York limited liability company ("Customer")',
           0.95, "Preamble"),
        _f("contract_title", "metadata",
           "Master Subscription Agreement",
           "MASTER SUBSCRIPTION AGREEMENT",
           0.99, "Header"),
        _f("effective_date", "metadata",
           "January 1, 2025",
           'entered into as of January 1, 2025 (the "Effective Date")',
           0.93, "Preamble"),
        _f("contract_term", "metadata",
           "Twelve (12) months",
           "The initial term of this Agreement is twelve (12) months, beginning on the Effective Date",
           0.94, "Section 2"),
        _f("renewal_terms", "metadata",
           "Automatically renews for successive one-year periods unless either party "
           "gives 60 days' non-renewal notice",
           "This Agreement shall automatically renew for successive one-year periods unless "
           "either party provides written notice of non-renewal at least sixty (60) days "
           "before the end of the then-current term.",
           0.92, "Section 4"),
        # --- Commercial terms --------------------------------------------------
        _f("setup_fee", "commercial_terms",
           "$10,000",
           "Customer shall pay a one-time setup fee of $10,000, invoiced upon execution of this Agreement.",
           0.96, "Section 3.1"),
        _f("recurring_fee", "commercial_terms",
           "$2,000 per month",
           "Customer shall pay a subscription fee of $2,000 per month for access to the Services.",
           0.97, "Section 3.2"),
        _f("recurring_fee_frequency", "commercial_terms",
           "Monthly",
           "Customer shall pay a subscription fee of $2,000 per month for access to the Services.",
           0.95, "Section 3.2"),
        _f("minimum_commitment", "commercial_terms",
           "$24,000 total over the Initial Term",
           "Customer commits to a minimum total contract value of $24,000 over the Initial Term.",
           0.90, "Section 3.4"),
        _f("usage_based_costs", "commercial_terms",
           "Queries over 1,000,000 per month are billed at $0.002 per query",
           "Analytics queries in excess of 1,000,000 per month are billed at $0.002 per query.",
           0.89, "Section 3.3"),
        _f("discount", "commercial_terms",
           None, None, None, None),  # intentionally no evidence -> NO_EVIDENCE
        _f("payment_terms", "commercial_terms",
           "Net 30",
           "All invoices are payable within thirty (30) days of receipt (Net 30).",
           0.96, "Section 3.6"),
        _f("price_increase_terms", "commercial_terms",
           "Up to 5% increase at each renewal",
           "Vendor may increase the subscription fee upon renewal by no more than five percent (5%) per renewal cycle.",
           0.91, "Section 5"),
        # --- Risk & operational terms ------------------------------------------
        # FABRICATED CLAIM: the contract says thirty (30) days; the fixture claims
        # ninety (90) days with a quote that does not exist in the document and
        # HIGH confidence (0.97). The deterministic verifier must catch this.
        _f("termination_notice", "risk_terms",
           "Termination requires 90 days' written notice",
           "Either party may terminate this Agreement for convenience upon ninety (90) "
           "days' prior written notice to the other party.",
           0.97, "Section 6"),
        _f("auto_renewal", "risk_terms",
           "Yes — automatic renewal for successive one-year periods",
           "This Agreement shall automatically renew for successive one-year periods unless "
           "either party provides written notice of non-renewal at least sixty (60) days "
           "before the end of the then-current term.",
           0.94, "Section 4"),
        _f("liability_cap", "risk_terms",
           "Cap equal to fees paid in the 12 months preceding the claim",
           "Vendor's total aggregate liability arising out of or related to this Agreement "
           "shall not exceed the total fees paid by Customer under this Agreement in the "
           "twelve (12) months preceding the event giving rise to the claim.",
           0.88, "Section 7"),
        _f("data_processing_terms", "risk_terms",
           "DPA applies; data encrypted in transit and at rest; 72-hour breach notice",
           "Vendor will process Customer data in accordance with the Data Processing "
           "Addendum attached as Exhibit A. Customer data is encrypted in transit and at rest.",
           0.87, "Section 8"),
        _f("governing_law", "risk_terms",
           "Delaware",
           "This Agreement is governed by the laws of the State of Delaware, without regard "
           "to conflict-of-laws principles.",
           0.97, "Section 9"),
    ]

    return ContractExtraction(
        fields={f.field_name: f for f in fields},
        # FABRICATED TCO: deterministic arithmetic gives $34,000 — the demo shows
        # ClauseGuard flagging the $16,000 discrepancy instead of trusting the model.
        ai_reported_tco="$50,000",
        raw_notes=(
            "SIMULATED extraction (demo fixture). Contains an intentionally unsupported "
            "termination claim and an intentionally incorrect reported TCO so the "
            "deterministic verification layer can be demonstrated. No real model call "
            "was made."
        ),
    )

