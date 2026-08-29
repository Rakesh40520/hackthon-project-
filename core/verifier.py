"""Deterministic evidence verification — the core differentiator.

This module NEVER asks an LLM whether an AI claim is correct. It performs a
pure text check: does the AI-provided evidence quote actually appear in the
source document after normalization?

Rules enforced here:
- VERIFIED only when the normalized evidence quote appears in the normalized source.
- UNVERIFIED when it does not (regardless of the model's confidence).
- NO_EVIDENCE when the model supplied no evidence quote at all.
- Model confidence is NOT an input to this function — it can never upgrade a result.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple

from core.schemas import VerificationResult, VerificationStatus

# Common typographic variants mapped to their plain-ASCII equivalents so that
# quotes copied out of PDFs/Word docs still match the source.
_QUOTE_MAP = {
    "\u2018": "'",   # left single curly quote
    "\u2019": "'",   # right single curly quote / apostrophe
    "\u201a": "'",   # single low quote
    "\u201b": "'",   # single high reversed quote
    "\u2039": "'",   # single guillemet
    "\u201c": '"',   # left double curly quote
    "\u201d": '"',   # right double curly quote
    "\u201e": '"',   # double low quote
    "\u201f": '"',   # double high reversed quote
    "\u00ab": '"',   # left guillemet
    "\u00bb": '"',   # right guillemet
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2010": "-",   # hyphen
    "\u2011": "-",   # non-breaking hyphen
    "\u2212": "-",   # minus sign
    "\u00a0": " ",   # no-break space
    "\u2007": " ",   # figure space
    "\u202f": " ",   # narrow no-break space
}

_ZERO_WIDTHS = ("\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad")


def normalize(text: str) -> str:
    """Normalize text for deterministic comparison.

    - Unicode NFKC compatibility normalization
    - Strip zero-width / soft-hyphen characters
    - Map curly quotes, dashes and exotic spaces to ASCII equivalents
    - Lowercase
    - Collapse all whitespace runs to single spaces
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", str(text))
    for ch in _ZERO_WIDTHS:
        t = t.replace(ch, "")
    for src, dst in _QUOTE_MAP.items():
        t = t.replace(src, dst)
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _alternatives(ch: str) -> List[str]:
    """All comparison-equivalent characters for `ch` (both map directions)."""
    alts = {ch}
    if ch in _QUOTE_MAP:
        alts.add(_QUOTE_MAP[ch])
    for src, dst in _QUOTE_MAP.items():
        if dst == ch:
            alts.add(src)
    return sorted(alts)


def _flexible_pattern(quote: str) -> str:
    """Build a regex that matches the quote in raw source text, tolerating
    whitespace differences and quote/dash character variants."""
    collapsed = " ".join(str(quote).split())
    token_patterns: List[str] = []
    for token in collapsed.split(" "):
        parts: List[str] = []
        for ch in token:
            alts = _alternatives(ch)
            if len(alts) > 1:
                parts.append("[" + "".join(re.escape(a) for a in alts) + "]")
            else:
                parts.append(re.escape(ch))
        token_patterns.append("".join(parts))
    return r"\s+".join(token_patterns)


def find_match_span(source_text: str, evidence_quote: str) -> Optional[Tuple[int, int]]:
    """Locate the quote inside the *raw* source text (for context display).

    Returns a (start, end) character span or None. This is display-only; the
    verified/unverified decision itself is made on normalized strings.
    """
    if not evidence_quote or not source_text:
        return None
    pattern = _flexible_pattern(evidence_quote)
    if not pattern:
        return None
    try:
        match = re.search(pattern, source_text, flags=re.IGNORECASE | re.DOTALL)
    except re.error:
        return None
    if not match:
        return None
    return match.start(), match.end()


def get_source_context(
    source_text: str,
    evidence_quote: str,
    context_chars: int = 280,
) -> Optional[str]:
    """Return the source text surrounding the matched evidence, if found."""
    span = find_match_span(source_text, evidence_quote)
    if span is None:
        return None
    start, end = span
    ctx_start = max(0, start - context_chars)
    ctx_end = min(len(source_text), end + context_chars)
    prefix = "…" if ctx_start > 0 else ""
    suffix = "…" if ctx_end < len(source_text) else ""
    snippet = source_text[ctx_start:ctx_end].strip()
    return f"{prefix}{snippet}{suffix}"


def verify(
    evidence_quote: Optional[str],
    source_text: Optional[str],
    include_context: bool = True,
    context_chars: int = 280,
) -> VerificationResult:
    """Deterministically verify that an evidence quote exists in the source.

    Note: `confidence` is intentionally NOT a parameter. A 99% confident claim
    with evidence that is not in the document is UNVERIFIED, full stop.
    """
    normalized_quote = normalize(evidence_quote or "")

    if not normalized_quote:
        return VerificationResult(
            status=VerificationStatus.NO_EVIDENCE,
            match_found=False,
            normalized_quote="",
            message="No source evidence was supplied for this claim.",
        )

    if not source_text or not source_text.strip():
        return VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            match_found=False,
            normalized_quote=normalized_quote,
            message=(
                "The source document text is unavailable or empty, so this claim "
                "could not be checked against the source."
            ),
        )

    normalized_source = normalize(source_text)

    if normalized_quote in normalized_source:
        context = None
        if include_context:
            context = get_source_context(source_text, evidence_quote, context_chars)
        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            match_found=True,
            normalized_quote=normalized_quote,
            message="Evidence was found in the uploaded contract.",
            context=context,
        )

    return VerificationResult(
        status=VerificationStatus.UNVERIFIED,
        match_found=False,
        normalized_quote=normalized_quote,
        message=(
            "The AI-provided evidence could not be found verbatim in the uploaded "
            "contract. This claim should not be treated as confirmed."
        ),
    )

