"""ClauseGuard — Verified Contract Intelligence (Streamlit UI).

The UI deliberately keeps business logic out: extraction lives in services/,
verification and arithmetic in core/. This file only orchestrates and renders.

Demo narrative:
  Most AI contract tools ask the model to read the contract and trust its answer.
  ClauseGuard treats the model as an untrusted extractor — it checks the evidence
  itself and independently verifies the math.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from core.schemas import (
    GROUP_LABELS,
    GROUP_ORDER,
    AnalysisResult,
    DocumentInfo,
    EvidenceField,
    TCOStatus,
    VerificationStatus,
)
from core.tco_calculator import calculate_tco
from core.verifier import verify
from services.demo_fixture import build_demo_extraction
from services.document_parser import ParsedDocument, parse_document_bytes
from services.llm_extractor import (
    ExtractorError,
    extract_contract,
    get_settings,
    is_llm_configured,
)
from services.number_parser import derive_pricing_inputs
from utils.formatting import (
    TCO_STATUS_LABELS,
    VERIFICATION_ICONS,
    VERIFICATION_LABELS,
    field_label,
    format_confidence,
    format_money,
)

load_dotenv()

st.set_page_config(
    page_title="ClauseGuard — Verified Contract Intelligence",
    page_icon="🛡️",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
SAMPLE_CONTRACT_PATH = ROOT / "sample_data" / "sample_contract.txt"

MODE_DEMO = "Demo fixture — simulated unreliable extraction"
MODE_LIVE = "Live LLM extraction"

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
      div[data-testid="stMetricValue"] { font-size: 1.35rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## ⚙️ Analysis Mode")
        configured = is_llm_configured()
        mode = st.radio(
            "Extraction source",
            [MODE_DEMO, MODE_LIVE],
            index=1 if configured else 0,
            help=(
                "Demo fixture simulates an unreliable extraction with planted errors "
                "so the verification layer can be demonstrated without an API key. "
                "Live mode sends your document to the configured LLM."
            ),
        )
        if configured:
            settings = get_settings()
            st.success(f"API key detected — model: `{settings['model']}`")
        else:
            st.warning(
                "No API key found. Live extraction is unavailable until you set "
                "`OPENAI_API_KEY` (see `.env.example`). The demo fixture works "
                "without a key."
            )

        st.divider()
        st.markdown("### How verification works")
        st.caption(
            "Every AI claim must include a verbatim evidence quote. ClauseGuard "
            "checks that quote against the actual document using deterministic "
            "code — never by asking the AI. Model confidence never overrides "
            "verification."
        )
        st.caption(
            "Total contract cost is recalculated independently with exact "
            "arithmetic and compared against whatever total the AI reported."
        )

        st.divider()
        st.caption(
            "ClauseGuard helps organize and verify contract information. "
            "It does not provide legal advice."
        )
    return mode


# ---------------------------------------------------------------------------
# Analysis pipeline (business logic delegated to core/ + services/)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _parse_cached(file_name: str, data: bytes) -> ParsedDocument:
    return parse_document_bytes(file_name, data)


def run_extraction(doc: ParsedDocument, mode: str) -> bool:
    """Run the full pipeline: extract -> verify -> derive pricing -> TCO.

    Returns True when an AnalysisResult was stored (safe to rerun the page).
    All failures are rendered as friendly errors, never raw stack traces.
    """
    is_demo = mode == MODE_DEMO
    debug: dict = {
        "mode": "demo" if is_demo else "live",
        "document": {
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "char_count": doc.char_count,
            "page_count": doc.page_count,
            "warnings": doc.warnings,
        },
    }

    try:
        if is_demo:
            with st.spinner("Running simulated demo extraction…"):
                time.sleep(0.5)  # brief pause so the demo flow reads naturally
                extraction = build_demo_extraction()
        else:
            with st.spinner(f"Extracting terms via LLM ({get_settings()['model']})…"):
                extraction, llm_debug = extract_contract(doc.text)
                debug.update(llm_debug)

        with st.spinner("Verifying evidence against the source document…"):
            verifications = {
                f.field_name: verify(f.evidence_quote, doc.text)
                for f in extraction.all_fields()
            }

        pricing = derive_pricing_inputs(extraction)

        with st.spinner("Cross-checking TCO arithmetic…"):
            tco = calculate_tco(
                **pricing.calculator_args,
                ai_reported_total=pricing.ai_reported_total,
            )
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
        st.session_state.analysis = analysis
        st.session_state.debug_info = debug
        return True

    except ExtractorError as exc:
        debug["error"] = str(exc)
        st.session_state.debug_info = debug
        st.error(f"**Extraction failed.** {exc}")
        return False
    except Exception as exc:  # defensive: never crash the UI with a stack trace
        debug["error"] = f"{type(exc).__name__}: {exc}"
        st.session_state.debug_info = debug
        st.error(
            "Something went wrong while analyzing this contract. Open the "
            "**Debug details** section at the bottom for developer information."
        )
        return False


# ---------------------------------------------------------------------------
# Header + upload
# ---------------------------------------------------------------------------

def render_header() -> None:
    st.markdown("# 🛡️ ClauseGuard")
    st.markdown("### Verified Contract Intelligence")
    st.markdown(
        "**Extract what matters. Verify what the AI claims.**  \n"
        "ClauseGuard treats the language model as an untrusted extractor: every "
        "claim must carry evidence that actually exists in your document, and "
        "the math is recalculated independently."
    )
    st.divider()


def render_upload(mode: str) -> None:
    uploaded = st.file_uploader(
        "Upload a contract (PDF, TXT or DOCX)",
        type=["pdf", "txt", "md", "docx"],
    )

    doc: Optional[ParsedDocument] = None
    if uploaded is not None:
        doc = _parse_cached(uploaded.name, uploaded.getvalue())
        info1, info2, info3, info4 = st.columns([2.4, 1, 1, 1])
        info1.markdown(f"**📄 {doc.file_name}**\n\nFile type: **{doc.file_type}**")
        info2.metric("Characters", f"{doc.char_count:,}")
        info3.metric("Pages", doc.page_count if doc.page_count else "—")
        info4.metric("Status", "Ready" if doc.ok else "Error")
        if doc.error:
            st.error(f"**Could not process this file.** {doc.error}")
        elif doc.warnings:
            st.warning(" ".join(doc.warnings))

    col_a, col_b, _spacer = st.columns([1.3, 1.6, 2.2])
    analyze_clicked = col_a.button(
        "Analyze & Verify Contract",
        type="primary",
        disabled=(uploaded is None),
        width="stretch",
    )
    demo_clicked = col_b.button(
        "🧪 Run built-in demo instead",
        help=(
            "Loads the bundled sample contract with a simulated unreliable "
            "extraction — no API key needed. Shows an unsupported claim and a "
            "TCO disagreement being caught."
        ),
        width="stretch",
    )

    if demo_clicked:
        sample_bytes = SAMPLE_CONTRACT_PATH.read_bytes()
        sample_doc = _parse_cached(SAMPLE_CONTRACT_PATH.name, sample_bytes)
        if sample_doc.ok:
            if run_extraction(sample_doc, MODE_DEMO):
                st.rerun()
        else:
            st.error(sample_doc.error)
    elif analyze_clicked and doc is not None:
        if doc.ok:
            if run_extraction(doc, mode):
                st.rerun()
        else:
            st.error(doc.error)


# ---------------------------------------------------------------------------
# Result rendering
# ---------------------------------------------------------------------------

def render_result(analysis: AnalysisResult) -> None:
    st.divider()
    st.caption(
        f"Showing analysis of **{analysis.document.file_name}** "
        f"(mode: {analysis.mode}, analyzed at {analysis.created_at})."
    )
    if analysis.mode == "demo":
        st.info(
            "🧪 **Demo mode** — this result comes from a *simulated, deliberately "
            "unreliable* extraction (one fabricated clause + one incorrect total) so "
            "you can watch the verification layer catch them. No real LLM call was "
            "made. Live analysis never injects false answers."
        )
    render_summary(analysis)
    render_attention(analysis)
    render_terms(analysis)
    render_tco(analysis)
    render_source(analysis)
    render_debug(analysis)


def render_summary(analysis: AnalysisResult) -> None:
    st.subheader("Summary Dashboard")
    tco = analysis.tco
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Fields extracted", analysis.extracted_count)
    m2.metric("✓ Verified", analysis.verified_count)
    m3.metric("⚠ Unverified", analysis.unverified_count)
    m4.metric("— No evidence", analysis.no_evidence_count)
    m5.metric("TCO status", TCO_STATUS_LABELS.get(tco.status, "—") if tco else "—")

    if analysis.unverified_count:
        st.error(
            f"**⚠ {analysis.unverified_count} AI claim(s) could not be verified "
            "against the source document.** Model confidence does not override "
            "verification — see *Claims Requiring Attention* below."
        )
    elif analysis.no_evidence_count:
        st.warning(
            f"{analysis.no_evidence_count} field(s) were reported without any "
            "evidence quote and should not be treated as confirmed."
        )
    else:
        st.success(
            "**✓ Every AI-provided evidence quote was found verbatim in the "
            "uploaded contract.**"
        )

    with st.expander("⬇ Export verification report (JSON)"):
        payload = json.dumps(analysis.model_dump(mode="json"), indent=2, default=str)
        st.download_button(
            "Download report",
            data=payload,
            file_name=f"clauseguard_report_{analysis.document.file_name or 'contract'}.json",
            mime="application/json",
        )


def render_attention(analysis: AnalysisResult) -> None:
    st.subheader("Claims Requiring Attention")
    flagged = analysis.attention_fields()
    if not flagged:
        st.success(
            "No unsupported claims — every asserted value carries evidence that "
            "was found in the document."
        )
        return

    st.error(
        f"**{len(flagged)} claim(s) need review.** The AI asserted the following, "
        "but the evidence does not hold up against the source document."
    )
    for f in flagged:
        v = analysis.verifications[f.field_name]
        if v.status is VerificationStatus.NO_EVIDENCE:
            headline = f"⚠ AI claim has no supporting evidence — {field_label(f.field_name)}"
        else:
            headline = f"⚠ AI claim could not be verified — {field_label(f.field_name)}"
        with st.container(border=True):
            st.markdown(f"#### {headline}")
            evidence = f'"{f.evidence_quote}"' if f.evidence_quote else "_(none supplied)_"
            st.markdown(
                f"**Field:** {field_label(f.field_name)}  \n"
                f"**AI-extracted value:** {f.value or '—'}  \n"
                f"**AI-provided evidence:** {evidence}  \n"
                f"**Why verification failed:** {v.message}"
            )
            if f.confidence is not None:
                st.caption(
                    f"Model confidence: {format_confidence(f.confidence)} — high "
                    "confidence does not make a claim verified. Only the source "
                    "document does."
                )


def _render_field_card(f: EvidenceField, analysis: AnalysisResult) -> None:
    v = analysis.verifications.get(f.field_name)
    if v is None:
        icon, label = "—", "— No evidence"
    else:
        icon = VERIFICATION_ICONS[v.status]
        label = VERIFICATION_LABELS[v.status]

    if f.value is None and (v is None or v.status is VerificationStatus.NO_EVIDENCE):
        title = f"— {field_label(f.field_name)} — not found"
    else:
        title = f"{icon} {field_label(f.field_name)} — {label}"

    with st.expander(title):
        st.markdown(f"**Extracted value:** {f.value or '—'}")
        st.markdown(f"**Source location hint:** {f.source_location_hint or '—'}")
        st.markdown("**AI-provided evidence quote:**")
        if f.evidence_quote:
            st.markdown(f"> {f.evidence_quote}")
        else:
            st.caption("The model supplied no evidence quote for this field.")

        if v is not None:
            if v.status is VerificationStatus.VERIFIED:
                st.success(f"✓ {v.message}")
                if v.context:
                    st.caption("Source context around the matched evidence:")
                    st.text(v.context)
            elif v.status is VerificationStatus.UNVERIFIED:
                st.error(f"⚠ {v.message}")
            else:
                st.info(f"— {v.message}")

        conf_line = f"Model confidence: {format_confidence(f.confidence)}"
        if (
            v is not None
            and v.status is not VerificationStatus.VERIFIED
            and f.confidence is not None
        ):
            conf_line += " — displayed for transparency only; it does not make this claim safe."
        st.caption(conf_line)


def render_terms(analysis: AnalysisResult) -> None:
    st.subheader("Extracted Terms")

    rows = []
    for f in analysis.extraction.all_fields():
        v = analysis.verifications.get(f.field_name)
        rows.append(
            {
                "Category": GROUP_LABELS.get(f.group, f.group),
                "Field": field_label(f.field_name),
                "Extracted Value": f.value or "—",
                "Verification": VERIFICATION_LABELS.get(v.status, "—") if v else "—",
                "Confidence": format_confidence(f.confidence),
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(
        "Confidence is the model's own self-assessment, shown for transparency "
        "only. Verification status is computed by ClauseGuard against the source "
        "document — a 99% confident but unverified claim is still unsafe."
    )

    for group in GROUP_ORDER:
        st.markdown(f"#### {GROUP_LABELS[group]}")
        group_fields = [f for f in analysis.extraction.all_fields() if f.group == group]
        for f in group_fields:
            _render_field_card(f, analysis)


def render_tco(analysis: AnalysisResult) -> None:
    tco = analysis.tco
    if tco is None:
        return
    st.subheader("Independent TCO Cross-Check")
    st.caption(
        "ClauseGuard recalculates totals independently rather than trusting the "
        "language model's arithmetic."
    )

    left, right = st.columns([1.1, 1.4])
    with left:
        st.markdown("**Extracted pricing inputs**")
        if analysis.pricing_rows:
            st.dataframe(
                pd.DataFrame(analysis.pricing_rows),
                width="stretch",
                hide_index=True,
            )
        else:
            st.caption("No pricing inputs were extracted.")
        for warning in analysis.pricing_warnings:
            st.warning(warning)
    with right:
        st.markdown("**Calculation breakdown**")
        st.code("\n".join(tco.calculation_steps) or "—", language="text")

    st.markdown("**Comparison**")
    c1, c2, c3 = st.columns(3)
    if tco.ai_reported_total is not None:
        ai_display = format_money(tco.ai_reported_total)
    elif tco.ai_reported_raw:
        ai_display = tco.ai_reported_raw
    else:
        ai_display = "—"
    c1.metric("AI-reported total", ai_display)
    c2.metric("Deterministic total", format_money(tco.calculated_total))
    c3.metric("Difference", format_money(tco.difference) if tco.difference is not None else "—")

    if tco.status is TCOStatus.DISAGREEMENT:
        st.error(
            "⚠ **Arithmetic disagreement detected**\n\n"
            f"AI-reported TCO: **{format_money(tco.ai_reported_total)}**  \n"
            f"Deterministic calculation: **{format_money(tco.calculated_total)}**  \n"
            f"Difference: **{format_money(tco.difference)}**\n\n"
            "The reported total does not match the extracted pricing terms."
        )
    elif tco.status is TCOStatus.MATCH:
        st.success(
            "✓ **Match** — the AI-reported TCO agrees with the deterministic "
            "calculation (within a small rounding tolerance)."
        )
    elif tco.status is TCOStatus.INSUFFICIENT_DATA:
        st.warning(f"**Insufficient data** — {tco.message}")
    else:
        st.info(
            "The AI did not report a total cost. The deterministic calculation "
            "is shown for reference."
        )

    for warning in tco.warnings:
        st.caption(f"Note: {warning}")


def render_source(analysis: AnalysisResult) -> None:
    st.subheader("Source Document")
    st.caption(
        "Verified claims above include the surrounding source context. Open the "
        "full text below to inspect any claim yourself."
    )
    with st.expander("📄 View full source text"):
        st.text_area(
            "Source text",
            value=analysis.source_text or "",
            height=420,
            disabled=True,
            label_visibility="collapsed",
        )


def render_debug(analysis: AnalysisResult) -> None:
    with st.expander("🔧 Debug details (developer)"):
        debug = st.session_state.get("debug_info") or {}
        payload = {
            "mode": analysis.mode,
            "created_at": analysis.created_at,
            "document": analysis.document.model_dump(mode="json"),
            "tco": analysis.tco.model_dump(mode="json") if analysis.tco else None,
            "field_count": len(analysis.extraction.fields),
            "debug": debug,
        }
        st.json(payload)


def render_footer() -> None:
    st.divider()
    st.caption(
        "ClauseGuard helps organize and verify contract information. "
        "It does not provide legal advice."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    render_header()
    mode = render_sidebar()
    render_upload(mode)
    analysis: Optional[AnalysisResult] = st.session_state.get("analysis")
    if analysis is not None:
        render_result(analysis)
    render_footer()


# Streamlit executes this script directly on every rerun.
main()






