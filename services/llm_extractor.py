"""LLM-backed contract extraction (OpenAI-compatible).

The model is treated strictly as an *untrusted extractor*. The prompt demands
verbatim evidence quotes and null-when-unknown; the deterministic verifier in
core.verifier independently decides whether to believe any of it.

Configuration via environment variables (see .env.example):
  OPENAI_API_KEY   — required for live extraction
  LLM_BASE_URL     — optional, any OpenAI-compatible endpoint
  LLM_MODEL        — optional, defaults to gpt-4o-mini
  LLM_TIMEOUT      — optional request timeout in seconds (default 120)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from core.schemas import ContractExtraction, FIELD_SPECS

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 120.0

# Contracts longer than this are truncated before being sent (with a warning).
MAX_CONTRACT_CHARS = 120_000


class ExtractorError(RuntimeError):
    """Raised for any failure during LLM extraction. Message is user-safe."""


def get_settings() -> Dict[str, Any]:
    """Read extractor configuration from the environment."""
    return {
        "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or "",
        "base_url": os.getenv("LLM_BASE_URL") or None,
        "model": os.getenv("LLM_MODEL") or DEFAULT_MODEL,
        "timeout": float(os.getenv("LLM_TIMEOUT") or DEFAULT_TIMEOUT),
    }


def is_llm_configured() -> bool:
    return bool(get_settings()["api_key"])


def _schema_block() -> str:
    """Describe the exact fields the model must extract."""
    lines: list = []
    for name, spec in FIELD_SPECS.items():
        lines.append(f'  - {spec["group"]}.{name}: {spec["description"]}')
    return "\n".join(lines)


def _json_template() -> str:
    """Show the model the exact JSON shape, with every field null."""
    return (
        '{\n'
        '  "metadata": {"vendor_name": {...}, "customer_name": {...}, "contract_title": {...}, '
        '"effective_date": {...}, "contract_term": {...}, "renewal_terms": {...}},\n'
        '  "commercial_terms": {"setup_fee": {...}, "recurring_fee": {...}, '
        '"recurring_fee_frequency": {...}, "minimum_commitment": {...}, "usage_based_costs": {...}, '
        '"discount": {...}, "payment_terms": {...}, "price_increase_terms": {...}},\n'
        '  "risk_terms": {"termination_notice": {...}, "auto_renewal": {...}, "liability_cap": {...}, '
        '"data_processing_terms": {...}, "governing_law": {...}},\n'
        '  "ai_reported_tco": null,\n'
        '  "raw_notes": null\n'
        '}'
    )


SYSTEM_PROMPT = """You are ClauseGuard's contract extraction engine. You extract structured \
commercial and legal terms from contracts. Your output will be mechanically verified against \
the source document, so accuracy of evidence is everything.

STRICT RULES — VIOLATIONS MAKE YOUR OUTPUT USELESS:
1. Never invent text. Never paraphrase evidence.
2. For every non-null field, "evidence_quote" MUST be a VERBATIM copy of a contiguous span of \
the provided contract text. Copy the characters exactly, including punctuation and phrasing.
3. If the contract does not explicitly contain the information, set BOTH "value" AND \
"evidence_quote" to null. Do not guess, infer, or fill gaps.
4. Do not infer legal or commercial terms that are not explicitly supported by the text.
5. "confidence" is a float between 0 and 1 reflecting how certain you are that the evidence \
quote is present in the document and supports the value. It will NOT be treated as proof.
6. "source_location_hint" is a short locator such as "Section 4" or "page 2".
7. For money fields, quote the amount exactly as written (e.g. "$10,000", "$2,000 per month").
8. For "ai_reported_tco": report the total contract cost implied by the pricing terms you \
extracted, as a plain string like "$34,000". If pricing is ambiguous or incomplete, return null. \
This figure will be independently cross-checked by deterministic arithmetic.
9. Return ONLY a single valid JSON object. No markdown fences, no commentary.

OUTPUT SHAPE (every listed field required; use null when unknown):
{json_template}

FIELDS TO EXTRACT:
{field_block}"""


def build_user_prompt(contract_text: str) -> str:
    return (
        "Extract the structured terms from the contract below. Follow the system rules exactly.\n\n"
        "<<<CONTRACT\n"
        f"{contract_text}\n"
        "CONTRACT>>>"
    )


def _clean_json_text(raw: str) -> str:
    """Strip markdown fences and grab the outermost JSON object."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model response")
    return text[start : end + 1]


def _call_llm(client: OpenAI, model: str, contract_text: str, use_json_mode: bool) -> Any:
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                json_template=_json_template(), field_block=_schema_block())},
            {"role": "user", "content": build_user_prompt(contract_text)},
        ],
        "temperature": 0,
    }
    if use_json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs)


def extract_contract(contract_text: str) -> Tuple[ContractExtraction, Dict[str, Any]]:
    """Run LLM extraction. Returns (ContractExtraction, debug_info).

    Raises ExtractorError with a user-safe message on any failure; the raw
    model output (if any) is included in debug_info for the debug panel.
    """
    settings = get_settings()
    if not settings["api_key"]:
        raise ExtractorError(
            "No API key configured. Set OPENAI_API_KEY in your environment or .env "
            "file (see .env.example), or use the built-in demo fixture."
        )

    truncated = contract_text[:MAX_CONTRACT_CHARS]
    client = OpenAI(
        api_key=settings["api_key"],
        base_url=settings["base_url"],
        timeout=settings["timeout"],
    )

    raw_content = ""
    try:
        try:
            response = _call_llm(client, settings["model"], truncated, use_json_mode=True)
        except Exception as exc:
            # Some OpenAI-compatible providers reject response_format; retry without it.
            if "response_format" in str(exc) or "json_object" in str(exc) or "json_schema" in str(exc):
                response = _call_llm(client, settings["model"], truncated, use_json_mode=False)
            else:
                raise
        raw_content = response.choices[0].message.content or ""
    except ExtractorError:
        raise
    except Exception as exc:
        raise ExtractorError(f"LLM request failed ({type(exc).__name__}): {exc}")

    try:
        parsed = json.loads(_clean_json_text(raw_content))
    except Exception as exc:
        snippet = (raw_content[:400] + "…") if len(raw_content) > 400 else raw_content
        raise ExtractorError(
            "The model returned invalid JSON. ClauseGuard will not guess its meaning. "
            f"({exc}) Raw output starts with: {snippet!r}"
        )

    try:
        extraction = ContractExtraction.from_raw(parsed)
    except Exception as exc:
        raise ExtractorError(f"The model's JSON did not match the extraction schema: {exc}")

    debug: Dict[str, Any] = {
        "model": settings["model"],
        "base_url": settings["base_url"] or "(default OpenAI)",
        "truncated_chars": max(0, len(contract_text) - len(truncated)),
        "raw_response": raw_content,
    }
    usage = getattr(response, "usage", None)
    if usage is not None:
        try:
            debug["token_usage"] = usage.model_dump()
        except Exception:
            pass
    return extraction, debug

