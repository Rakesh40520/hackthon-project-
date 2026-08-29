"""Conservative monetary & term parsing.

Design rule: this parser would rather return "I don't know" than guess.
Ambiguous pricing language ("fees may vary", "pricing to be mutually agreed",
ranges, multiple amounts) produces a warning + no value — never a fabricated
number that downstream arithmetic could silently trust.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from core.schemas import ContractExtraction
from utils.formatting import field_label, format_money


# ---------------------------------------------------------------------------
# Money parsing
# ---------------------------------------------------------------------------

@dataclass
class ParsedMoney:
    value: Optional[Decimal] = None
    original: str = ""
    ambiguous: bool = False
    warning: Optional[str] = None
    frequency_hint: Optional[str] = None


_MONEY_RE = re.compile(
    r"(?:(?P<cur>[$€£])\s?|\busd\s*)?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Phrases that mean "there is no confidently parseable amount here".
_AMBIGUOUS_PHRASES = [
    "vary", "varies", "variable", "subject to change", "mutually agreed",
    "to be agreed", "to be determined", "to be negotiated", "tbd",
    "custom pricing", "contact us", "enterprise pricing", "quoted separately",
    "negotiated separately", "pricing schedule", "estimate",
]

_RANGE_HINTS = ["between ", " up to ", "starting at", "starting from", "from $", "from usd"]

_FREQUENCY_PATTERNS = [
    ("monthly", re.compile(r"per month|/month|/mo\b|monthly|each month", re.I)),
    ("annual", re.compile(r"per year|/year|/yr\b|annual|annually|per annum", re.I)),
    ("quarterly", re.compile(r"per quarter|/quarter|quarterly", re.I)),
    ("weekly", re.compile(r"per week|/week|weekly", re.I)),
]


def _detect_frequency(text: str) -> Optional[str]:
    """Return a frequency hint, or 'unsupported' for weekly/daily billing."""
    for name, pattern in _FREQUENCY_PATTERNS:
        if pattern.search(text):
            return name
    return None


def parse_money(text: Any) -> ParsedMoney:
    """Parse a monetary amount conservatively.

    Handles: $10,000 | USD 10,000 | $2,500/month | $30,000 per year | 10000.
    Returns ParsedMoney with value=None + warning when the text is ambiguous.
    """
    if text is None:
        return ParsedMoney(original="")
    s = str(text).strip()
    if not s:
        return ParsedMoney(original="")

    low = s.lower()
    for phrase in _AMBIGUOUS_PHRASES:
        if phrase in low:
            return ParsedMoney(
                original=s,
                ambiguous=True,
                warning=(f'Cannot confidently parse an amount from "{s}" '
                         f"(ambiguous pricing language)."),
            )
    for hint in _RANGE_HINTS:
        if hint in low:
            return ParsedMoney(
                original=s,
                ambiguous=True,
                warning=(f'"{s}" looks like a range or starting price; refusing '
                         f"to pick a single number."),
            )

    values: List[Decimal] = []
    for match in _MONEY_RE.finditer(s):
        raw_num = match.group("num").replace(",", "")
        try:
            values.append(Decimal(raw_num))
        except InvalidOperation:
            continue

    if not values:
        return ParsedMoney(
            original=s,
            ambiguous=True,
            warning=f'No monetary amount could be parsed from "{s}".',
        )

    distinct = sorted(set(values))
    if len(distinct) > 1:
        return ParsedMoney(
            original=s,
            ambiguous=True,
            warning=(f'Multiple different amounts found in "{s}"; refusing to pick one.'),
        )

    freq = _detect_frequency(low)
    if freq == "weekly":
        return ParsedMoney(
            original=s,
            value=distinct[0],
            ambiguous=True,
            warning=f'Weekly billing in "{s}" is not supported by the calculator.',
        )

    return ParsedMoney(original=s, value=distinct[0], frequency_hint=freq)


# ---------------------------------------------------------------------------
# Term (duration) parsing
# ---------------------------------------------------------------------------

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "eighteen": 18, "twenty": 20, "twenty-four": 24, "twenty four": 24,
    "thirty": 30, "thirty-six": 36, "thirty six": 36, "forty-eight": 48,
    "forty eight": 48, "sixty": 60,
}

_TERM_RE = re.compile(
    r"(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"eighteen|twenty|thirty|forty|fifty|sixty)"
    r"(?:\s*\(\s*\d+\s*\))?\s*[-–—]?\s*"
    r"(?P<unit>month|months|year|years|yr|yrs|week|weeks)\b",
    re.IGNORECASE,
)

_PAREN_NUM_RE = re.compile(r"\(\s*(\d+)\s*\)")


def parse_term_months(text: Any) -> tuple:
    """Parse a contract term into months.

    Returns (months: Optional[int], warning: Optional[str]).
    Conservative: multiple *different* term lengths yield (None, warning).
    """
    if text is None or not str(text).strip():
        return None, "No contract term information was provided."

    s = str(text)
    months_found: List[int] = []

    for match in _TERM_RE.finditer(s):
        n_raw = match.group("n")
        unit = match.group("unit").lower()

        # Prefer an explicit parenthesized numeral: "twelve (12) months" -> 12.
        paren = _PAREN_NUM_RE.search(match.group(0))
        if paren:
            n = int(paren.group(1))
        elif n_raw.isdigit():
            n = int(n_raw)
        else:
            n = _WORD_NUMBERS.get(n_raw.lower().replace("-", " ").strip())
            if n is None:
                continue

        if unit.startswith("month"):
            months_found.append(n)
        elif unit.startswith("year") or unit in ("yr", "yrs"):
            months_found.append(n * 12)
        else:  # weeks are not a supported contract granularity
            return None, f'Week-based terms ("{match.group(0)}") are not supported.'

    if not months_found:
        return None, f'Could not parse a term length from "{text}".'

    distinct = sorted(set(months_found))
    if len(distinct) > 1:
        return None, (
            f'Multiple different term lengths found in "{text}"; '
            "refusing to pick one."
        )
    return distinct[0], None


def parse_frequency_text(text: Any) -> tuple:
    """Parse a billing-frequency description.

    Returns (frequency: Optional[str], warning: Optional[str]).
    """
    if text is None or not str(text).strip():
        return None, None
    low = str(text).lower()
    freq = _detect_frequency(low)
    if freq == "weekly":
        return None, "Weekly billing is not supported by the calculator."
    if freq is None:
        return None, f'Could not determine a billing frequency from "{text}".'
    return freq, None


# ---------------------------------------------------------------------------
# Extraction -> deterministic pricing inputs
# ---------------------------------------------------------------------------

@dataclass
class PricingInputs:
    """Numeric inputs for the TCO calculator, derived conservatively."""

    setup_fee: Optional[Decimal] = None
    recurring_fee: Optional[Decimal] = None
    frequency: Optional[str] = None
    term_months: Optional[int] = None
    minimum_commitment: Optional[Decimal] = None  # always total-over-term
    usage_cost: Optional[Decimal] = None
    ai_reported_total: Optional[Decimal] = None
    ai_reported_raw: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    input_rows: List[Dict[str, str]] = field(default_factory=list)

    @property
    def calculator_args(self) -> Dict[str, Any]:
        return {
            "setup_fee": self.setup_fee,
            "recurring_fee": self.recurring_fee,
            "frequency": self.frequency,
            "term_months": self.term_months,
            "minimum_commitment": self.minimum_commitment,
            "usage_cost": self.usage_cost,
        }


def _field_value(extraction: ContractExtraction, name: str) -> Optional[str]:
    f = extraction.get(name)
    return f.value if f else None


def _money_row(label: str, parsed: Optional[ParsedMoney], used: Optional[Decimal]) -> Dict[str, str]:
    return {
        "Input": label,
        "Value used": format_money(used) if used is not None else "—",
        "Source text": (parsed.original if parsed and parsed.original else "—"),
    }


def derive_pricing_inputs(extraction: ContractExtraction) -> PricingInputs:
    """Convert extracted (textual) pricing fields into conservative numbers.

    Every ambiguity becomes a warning — never an assumption baked into math.
    """
    result = PricingInputs()
    warnings = result.warnings

    # --- Setup fee -----------------------------------------------------------
    setup_raw = _field_value(extraction, "setup_fee")
    setup_pm = parse_money(setup_raw) if setup_raw else None
    if setup_raw:
        if setup_pm.ambiguous:
            warnings.append(f"Setup fee: {setup_pm.warning}")
        else:
            result.setup_fee = setup_pm.value
        result.input_rows.append(_money_row("Setup fee", setup_pm, result.setup_fee))

    # --- Recurring fee ---------------------------------------------------------
    rec_raw = _field_value(extraction, "recurring_fee")
    rec_pm = parse_money(rec_raw) if rec_raw else None
    if rec_raw:
        if rec_pm.ambiguous:
            warnings.append(f"Recurring fee: {rec_pm.warning}")
        else:
            result.recurring_fee = rec_pm.value
        result.input_rows.append(_money_row("Recurring fee", rec_pm, result.recurring_fee))

    # --- Billing frequency -------------------------------------------------------
    freq_raw = _field_value(extraction, "recurring_fee_frequency")
    frequency, freq_warn = parse_frequency_text(freq_raw)
    if freq_warn:
        warnings.append(f"Billing frequency: {freq_warn}")
    if frequency is None and rec_pm is not None and not rec_pm.ambiguous and rec_pm.frequency_hint:
        frequency = rec_pm.frequency_hint
    result.frequency = frequency
    result.input_rows.append(
        {
            "Input": "Billing frequency",
            "Value used": frequency or "—",
            "Source text": freq_raw or rec_raw or "—",
        }
    )

    # --- Contract term -----------------------------------------------------------
    term_raw = _field_value(extraction, "contract_term")
    months, term_warn = parse_term_months(term_raw)
    if term_warn:
        warnings.append(f"Contract term: {term_warn}")
    result.term_months = months
    result.input_rows.append(
        {
            "Input": "Contract term",
            "Value used": f"{months} months" if months is not None else "—",
            "Source text": term_raw or "—",
        }
    )

    # --- Minimum commitment --------------------------------------------------------
    min_raw = _field_value(extraction, "minimum_commitment")
    if min_raw:
        min_pm = parse_money(min_raw)
        if min_pm.ambiguous or min_pm.value is None:
            warnings.append(f"Minimum commitment: {min_pm.warning}")
        else:
            low = min_raw.lower()
            if "per month" in low or "/month" in low or "monthly" in low:
                if months:
                    result.minimum_commitment = min_pm.value * months
                    warnings.append(
                        "Minimum commitment is stated per month; it was multiplied by "
                        "the term length for the deterministic check."
                    )
                else:
                    warnings.append(
                        "Minimum commitment is per month but the term is unknown; "
                        "it is excluded from the calculation."
                    )
            else:
                result.minimum_commitment = min_pm.value
                warnings.append(
                    "Minimum commitment is assumed to be a total over the contract "
                    "term (the contract does not state a per-month basis)."
                )
        result.input_rows.append(_money_row("Minimum commitment", min_pm, result.minimum_commitment))

    # --- Usage-based costs -----------------------------------------------------------
    usage_raw = _field_value(extraction, "usage_based_costs")
    if usage_raw:
        low = usage_raw.lower()
        if "per " in low or "/query" in low or "/gb" in low or "/seat" in low or "per-" in low:
            warnings.append(
                "Usage-based cost appears to be unit-priced (e.g. per query); total "
                "usage spend cannot be determined deterministically, so it is "
                "excluded from the calculation."
            )
            result.input_rows.append(
                {"Input": "Usage-based cost", "Value used": "excluded (unit-priced)", "Source text": usage_raw}
            )
        else:
            usage_pm = parse_money(usage_raw)
            if usage_pm.ambiguous or usage_pm.value is None:
                warnings.append(f"Usage-based cost: {usage_pm.warning}")
                result.input_rows.append(
                    {"Input": "Usage-based cost", "Value used": "— (unparsable)", "Source text": usage_raw}
                )
            else:
                result.usage_cost = usage_pm.value
                warnings.append("A stated usage cost was included as an explicit amount.")
                result.input_rows.append(_money_row("Usage-based cost", usage_pm, result.usage_cost))

    # --- AI-reported TCO ---------------------------------------------------------------
    ai_raw = extraction.ai_reported_tco
    if ai_raw:
        ai_pm = parse_money(ai_raw)
        result.ai_reported_raw = ai_pm.original or ai_raw
        if ai_pm.ambiguous or ai_pm.value is None:
            warnings.append(f"AI-reported TCO: {ai_pm.warning}")
        else:
            result.ai_reported_total = ai_pm.value
        result.input_rows.append(_money_row("AI-reported TCO", ai_pm, result.ai_reported_total))

    return result



