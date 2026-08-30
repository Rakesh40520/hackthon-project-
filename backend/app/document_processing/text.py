"""CSV and TXT extraction."""
from __future__ import annotations

import csv
from typing import List

from app.document_processing.extractor import ExtractedDocument, ExtractedSection


def extract_csv(file_path: str, filename: str) -> ExtractedDocument:
    with open(file_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        rows: List[List[str]] = [r for r in reader if r]
    text = "\n".join(",".join(r) for r in rows)
    return ExtractedDocument(
        text=text,
        sections=[ExtractedSection(text=text, document=filename)],
        tables=[rows] if rows else [],
        metadata={"filename": filename, "type": "csv"},
    )


def extract_txt(file_path: str, filename: str) -> ExtractedDocument:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return ExtractedDocument(
        text=text,
        sections=[ExtractedSection(text=text, document=filename)],
        metadata={"filename": filename, "type": "txt"},
    )
