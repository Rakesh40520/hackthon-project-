"""Document text extraction and concatenation."""
from __future__ import annotations

import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.document_processing import DocumentExtractor
from app.models import Proposal, ProposalDocument

logger = logging.getLogger(__name__)


async def run_extraction(db: AsyncSession, proposal: Proposal) -> str:
    docs_res = await db.execute(
        select(ProposalDocument).where(ProposalDocument.proposal_id == proposal.id)
    )
    docs = docs_res.scalars().all()
    combined_parts: List[str] = []
    for d in docs:
        extractor = DocumentExtractor(d.storage_path, original_filename=d.filename)
        ed = extractor.extract()
        if ed.error:
            logger.warning("Extraction error for %s: %s", d.filename, ed.error)
            continue
        d.page_count = ed.page_count
        if ed.text:
            combined_parts.append(f"=== Document: {d.filename} ===\n{ed.text}")
    proposal.extracted_text = "\n\n".join(combined_parts)
    await db.commit()
    return proposal.extracted_text or ""


def _chunk_text(text: str, max_chars: int = 24000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...truncated...]"
