"""Shared ClauseGuard analysis pipeline (framework-free).

Runs the full flow for one document:

    parse (done by caller) -> extract (demo fixture or live LLM)
        -> deterministic verification of every field
        -> conservative pricing derivation
        -> independent TCO calculation

Returns an AnalysisResult plus a debug dict. Contains no UI or framework
code, so it can be reused by any frontend (web, Streamlit, CLI, tests).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from core.schemas import AnalysisResult, DocumentInfo
from core.tco_calculator import calculate_tco
from core.verifier import verify
from services.demo_fixture import build_demo_extraction
from services.document_parser import ParsedDocument
from services.llm_extractor import extract_contract, get_settings
from services.number_parser import derive_pricing_inputs


def run_analysis_pipeline(doc: ParsedDocument, mode: str) -> Tuple[AnalysisResult, Dict[str, Any]]:
    """Analyze a parsed document. mode is 'demo' or 'live'.

    Raises services.llm_extractor.ExtractorError for live-mode failures; all
    other exceptions are unexpected bugs and propagate to the caller's handler.
    """
    is_demo = mode == "demo"
    debug: Dict[str, Any] = {
        "mode": "demo" if is_demo else "live",
        "document": {
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "char_count": doc.char_count,
            "page_count": doc.page_count,
            "warnings": list(doc.warnings),
        },
    }

    if is_demo:
        extraction = build_demo_extraction()
    else:
        extraction, llm_debug = extract_contract(doc.text)
        debug.update(llm_debug)

    verifications = {
        f.field_name: verify(f.evidence_quote, doc.text)
        for f in extraction.all_fields()
    }

    pricing = derive_pricing_inputs(extraction)
    tco = calculate_tco(**pricing.calculator_args, ai_reported_total=pricing.ai_reported_total)
    tco.ai_reported_raw = pricing.ai_reported_raw

    analysis = AnalysisResult(
        mode="demo" if is_demo else "live",
        created_at=datetime.now().isoformat(timespec="seconds"),
        document=DocumentInfo(
            file_name=doc.file_name,
            file_type=doc.file_type,
            char_count=doc.char_count,
            page_count=doc.page_count,
            warnings=list(doc.warnings),
        ),
        extraction=extraction,
        verifications=verifications,
        tco=tco,
        pricing_rows=pricing.input_rows,
        pricing_warnings=pricing.warnings,
        source_text=doc.text,
    )
    debug["pricing_warnings"] = pricing.warnings
    return analysis, debug
