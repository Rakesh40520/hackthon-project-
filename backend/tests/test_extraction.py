"""Document extraction tests."""
from __future__ import annotations

from app.document_processing import DocumentExtractor


def test_extract_txt(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Hello World\nThis is a test proposal.", encoding="utf-8")
    ex = DocumentExtractor(str(p), "sample.txt")
    res = ex.extract()
    assert "Hello World" in res.text
    assert res.error is None


def test_extract_csv(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text("name,price\nService A,1000\nService B,2000\n", encoding="utf-8")
    ex = DocumentExtractor(str(p), "sample.csv")
    res = ex.extract()
    assert "Service A" in res.text
    assert res.tables
