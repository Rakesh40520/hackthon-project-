"""PDF extraction."""
from __future__ import annotations

import logging
from typing import List

from app.document_processing.extractor import ExtractedDocument, ExtractedSection

logger = logging.getLogger(__name__)


def extract_pdf(file_path: str, filename: str) -> ExtractedDocument:
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    sections: List[ExtractedSection] = []
    full_text_parts: List[str] = []
    for page_idx, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        if text.strip():
            sections.append(ExtractedSection(text=text, page=page_idx, document=filename))
            full_text_parts.append(text)
    page_count = doc.page_count
    doc.close()
    return ExtractedDocument(
        text="\n\n".join(full_text_parts),
        sections=sections,
        page_count=page_count,
        metadata={"filename": filename, "type": "pdf"},
    )
