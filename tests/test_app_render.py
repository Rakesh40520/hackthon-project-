"""UI-level smoke tests using Streamlit's AppTest framework.

These run app.py in-process and fail if any Streamlit exception occurs while
rendering (e.g., a bad import, a typo in a render function, a schema mismatch).

Run:  python tests/test_app_render.py     (or: pytest tests/test_app_render.py)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

from core.schemas import AnalysisResult, DocumentInfo
from core.tco_calculator import calculate_tco
from core.verifier import verify
from services.demo_fixture import build_demo_extraction
from services.document_parser import parse_document_bytes
from services.number_parser import derive_pricing_inputs

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
SAMPLE_PATH = ROOT / "sample_data" / "sample_contract.txt"


def _build_analysis() -> AnalysisResult:
    """Mirror of app.run_extraction for the demo fixture (no UI calls)."""
    doc = parse_document_bytes(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes())
    extraction = build_demo_extraction()
    verifications = {
        f.field_name: verify(f.evidence_quote, doc.text)
        for f in extraction.all_fields()
    }
    pricing = derive_pricing_inputs(extraction)
    tco = calculate_tco(**pricing.calculator_args, ai_reported_total=pricing.ai_reported_total)
    tco.ai_reported_raw = pricing.ai_reported_raw
    return AnalysisResult(
        mode="demo",
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


def test_app_boots_without_exception() -> None:
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    # Sidebar mode selector and the file uploader should be present.
    assert len(at.radio) == 1
    assert len(at.file_uploader) == 1


def test_app_renders_demo_result_without_exception() -> None:
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.session_state["analysis"] = _build_analysis()
    at.session_state["debug_info"] = {"mode": "demo"}
    at.run()
    assert not at.exception, at.exception
    # The demo analysis should surface metrics, warnings and the TCO card.
    metric_labels = [m.label for m in at.metric]
    assert "✓ Verified" in metric_labels
    assert "⚠ Unverified" in metric_labels
    assert "AI-reported total" in metric_labels
    assert "Deterministic total" in metric_labels
    assert "Difference" in metric_labels
    # Both demo moments must be visible: unverified-claim alerts and TCO errors.
    error_texts = " ".join(e.value for e in at.error)
    assert "could not be verified" in error_texts
    assert "Arithmetic disagreement detected" in error_texts


def main() -> int:
    tests = [
        ("UI: app boots without exception", test_app_boots_without_exception),
        ("UI: demo result renders without exception", test_app_renders_demo_result_without_exception),
    ]
    passed = failed = 0
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
