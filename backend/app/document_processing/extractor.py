"""Extract text and tables from PDF, DOCX, XLSX, CSV, TXT."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSection:
    """A piece of text with location info."""

    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    document: Optional[str] = None


@dataclass
class ExtractedDocument:
    """Result of document extraction."""

    text: str = ""
    sections: List[ExtractedSection] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: Optional[int] = None
    error: Optional[str] = None


class DocumentExtractor:
    """Multi-format document extractor."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}

    def __init__(self, file_path: str, original_filename: Optional[str] = None):
        self.file_path = file_path
        self.filename = original_filename or os.path.basename(file_path)
        self.ext = os.path.splitext(self.filename)[1].lower()

    def extract(self) -> ExtractedDocument:
        try:
            if self.ext == ".pdf":
                from app.document_processing.pdf import extract_pdf
                return extract_pdf(self.file_path, self.filename)
            if self.ext == ".docx":
                from app.document_processing.docx import extract_docx
                return extract_docx(self.file_path, self.filename)
            if self.ext == ".xlsx":
                from app.document_processing.xlsx import extract_xlsx
                return extract_xlsx(self.file_path, self.filename)
            if self.ext == ".csv":
                from app.document_processing.text import extract_csv
                return extract_csv(self.file_path, self.filename)
            if self.ext == ".txt":
                from app.document_processing.text import extract_txt
                return extract_txt(self.file_path, self.filename)
            return ExtractedDocument(error=f"Unsupported file type: {self.ext}")
        except Exception as e:  # pragma: no cover
            logger.exception("Extraction failed for %s", self.filename)
            return ExtractedDocument(error=str(e))
