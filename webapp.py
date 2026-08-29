"""ClauseGuard — custom web application (Flask).

A dedicated browser UI on top of the same deterministic engine used by the
Streamlit dashboard:

    GET  /               landing page with upload form + demo button
    POST /analyze        runs the pipeline, redirects to the report page
    GET  /results/<id>   full verification report (terms, alerts, TCO, source)
    GET  /download/<id>  JSON report download
    GET  /health         simple liveness endpoint

Results are held in an in-memory store keyed by an analysis id — no database
is required. Errors are rendered as friendly pages, never raw stack traces.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, Response, abort, redirect, render_template, request, url_for

from core.schemas import (
    GROUP_LABELS,
    GROUP_ORDER,
    AnalysisResult,
    EvidenceField,
    TCOStatus,
    VerificationStatus,
)
from services.document_parser import ParsedDocument, parse_document_bytes
from services.llm_extractor import ExtractorError, get_settings, is_llm_configured
from services.pipeline import run_analysis_pipeline
from utils.formatting import (
    TCO_STATUS_LABELS,
    VERIFICATION_ICONS,
    VERIFICATION_LABELS,
    field_label,
    format_confidence,
    format_money,
)

ROOT = Path(__file__).resolve().parent
SAMPLE_CONTRACT_PATH = ROOT / "sample_data" / "sample_contract.txt"
MAX_UPLOAD_BYTES = 16 * 1024 * 1024  # 16 MB

app = Flask(__name__)
# Session key only (not an API secret): random per process, or set FLASK_SECRET_KEY.
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# In-memory result store — sufficient for demos; survives for the process lifetime.
ANALYSES: Dict[str, AnalysisResult] = {}
DEBUG_INFO: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# View-model builders (keep templates free of business logic)
# ---------------------------------------------------------------------------

def _field_view(f: EvidenceField, analysis: AnalysisResult) -> Dict[str, Any]:
    v = analysis.verifications.get(f.field_name)
    verified = v is not None and v.status is VerificationStatus.VERIFIED
    unverified = v is not None and v.status is VerificationStatus.UNVERIFIED
    return {
        "label": field_label(f.field_name),
        "value": f.value or "—",
        "hint": f.source_location_hint or "—",
        "evidence": f.evidence_quote,
        "icon": VERIFICATION_ICONS.get(v.status, "—") if v else "—",
        "status_label": VERIFICATION_LABELS.get(v.status, "— No evidence") if v else "— No evidence",
        "status_code": "ok" if verified else ("bad" if unverified else "none"),
        "message": v.message if v else "",
        "context": v.context if v else None,
        "confidence": format_confidence(f.confidence),
        "conf_note": (
            "displayed for transparency only; it does not make this claim safe."
            if (unverified and f.confidence is not None)
            else ""
        ),
        "not_found": f.value is None and (v is None or v.status is VerificationStatus.NO_EVIDENCE),
    }


def _groups_view(analysis: AnalysisResult) -> list:
    groups = []
    for group in GROUP_ORDER:
        groups.append(
            {
                "label": GROUP_LABELS.get(group, group),
                "fields": [
                    _field_view(f, analysis)
                    for f in analysis.extraction.all_fields()
                    if f.group == group
                ],
            }
        )
    return groups


def _attention_view(analysis: AnalysisResult) -> list:
    items = []
    for f in analysis.attention_fields():
        v = analysis.verifications[f.field_name]
        items.append(
            {
                "label": field_label(f.field_name),
                "value": f.value or "—",
                "evidence": f.evidence_quote,
                "message": v.message,
                "confidence": format_confidence(f.confidence),
                "kind": "no_evidence" if v.status is VerificationStatus.NO_EVIDENCE else "unverified",
            }
        )
    return items


def _summary_view(analysis: AnalysisResult) -> Dict[str, Any]:
    if analysis.unverified_count:
        banner = {
            "kind": "danger",
            "text": (
                f"⚠ {analysis.unverified_count} AI claim(s) could not be verified "
                "against the source document. Model confidence does not override "
                "verification — see Claims Requiring Attention."
            ),
        }
    elif analysis.no_evidence_count:
        banner = {
            "kind": "warn",
            "text": (
                f"{analysis.no_evidence_count} field(s) were reported without any "
                "evidence quote and should not be treated as confirmed."
            ),
        }
    else:
        banner = {
            "kind": "ok",
            "text": "✓ Every AI-provided evidence quote was found verbatim in the uploaded contract.",
        }
    return {
        "extracted": analysis.extracted_count,
        "verified": analysis.verified_count,
        "unverified": analysis.unverified_count,
        "no_evidence": analysis.no_evidence_count,
        "tco_label": TCO_STATUS_LABELS.get(analysis.tco.status, "—") if analysis.tco else "—",
        "banner": banner,
    }


def _tco_view(analysis: AnalysisResult) -> Optional[Dict[str, Any]]:
    tco = analysis.tco
    if tco is None:
        return None

    if tco.ai_reported_total is not None:
        ai_display = format_money(tco.ai_reported_total)
    elif tco.ai_reported_raw:
        ai_display = tco.ai_reported_raw
    else:
        ai_display = "—"

    if tco.status is TCOStatus.DISAGREEMENT:
        banner = {
            "kind": "danger",
            "title": "⚠ Arithmetic disagreement detected",
            "lines": [
                f"AI-reported TCO: {format_money(tco.ai_reported_total)}",
                f"Deterministic calculation: {format_money(tco.calculated_total)}",
                f"Difference: {format_money(tco.difference)}",
                "The reported total does not match the extracted pricing terms.",
            ],
        }
    elif tco.status is TCOStatus.MATCH:
        banner = {
            "kind": "ok",
            "title": "✓ Match",
            "lines": [
                "The AI-reported TCO agrees with the deterministic calculation "
                "(within a small rounding tolerance)."
            ],
        }
    elif tco.status is TCOStatus.INSUFFICIENT_DATA:
        banner = {"kind": "warn", "title": "⚠ Insufficient data", "lines": [tco.message]}
    else:
        banner = {
            "kind": "info",
            "title": "AI total not provided",
            "lines": [
                "The AI did not report a total cost. The deterministic calculation "
                "is shown for reference."
            ],
        }

    return {
        "rows": analysis.pricing_rows,
        "pricing_warnings": analysis.pricing_warnings,
        "steps": tco.calculation_steps,
        "ai_display": ai_display,
        "deterministic": format_money(tco.calculated_total),
        "difference": format_money(tco.difference) if tco.difference is not None else "—",
        "banner": banner,
        "warnings": tco.warnings,
        "status_label": TCO_STATUS_LABELS.get(tco.status, "—"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        configured=is_llm_configured(),
        model=get_settings()["model"],
        sample_available=SAMPLE_CONTRACT_PATH.exists(),
    )


@app.route("/health")
def health():
    return {"status": "ok", "analyses_in_memory": len(ANALYSES)}


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = "demo" if request.form.get("demo") == "1" else request.form.get("mode", "demo")

    def fail(message: str, details: str = ""):
        return render_template(
            "index.html",
            error=message,
            error_details=details,
            configured=is_llm_configured(),
            model=get_settings()["model"],
            selected_mode=mode,
            sample_available=SAMPLE_CONTRACT_PATH.exists(),
        )

    if mode == "live" and not is_llm_configured():
        return fail(
            "Live extraction needs an API key. Set OPENAI_API_KEY in your .env "
            "file (see .env.example), or run the demo instead."
        )

    # --- Obtain the document -------------------------------------------------
    if request.form.get("demo") == "1":
        if not SAMPLE_CONTRACT_PATH.exists():
            return fail("The built-in sample contract is missing from sample_data/.")
        doc = parse_document_bytes(SAMPLE_CONTRACT_PATH.name, SAMPLE_CONTRACT_PATH.read_bytes())
    else:
        upload = request.files.get("contract")
        if upload is None or not upload.filename:
            return fail("Please choose a contract file (PDF, TXT or DOCX) to analyze.")
        filename = os.path.basename(upload.filename).strip() or "contract"
        data = upload.read()
        if len(data) > MAX_UPLOAD_BYTES:
            return fail("That file is larger than the 16 MB limit.")
        doc = parse_document_bytes(filename, data)

    if doc.error:
        return fail(f"Could not process '{doc.file_name}'. {doc.error}")

    # --- Run the pipeline ------------------------------------------------------
    try:
        analysis, debug = run_analysis_pipeline(doc, mode)
    except ExtractorError as exc:
        return fail(f"Extraction failed. {exc}")
    except Exception as exc:  # defensive: friendly page, details for developers
        return fail(
            "Something went wrong while analyzing this contract.",
            details=f"{type(exc).__name__}: {exc}",
        )

    analysis_id = uuid.uuid4().hex[:12]
    ANALYSES[analysis_id] = analysis
    DEBUG_INFO[analysis_id] = debug
    return redirect(url_for("results", analysis_id=analysis_id))



