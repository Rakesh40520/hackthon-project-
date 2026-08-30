"""Misc helpers."""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def slugify(value: str, max_length: int = 80) -> str:
    """Return a URL-safe slug for a string."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return (value or "item")[:max_length]


def safe_float(value) -> Optional[float]:
    """Parse a float safely, returning None on failure."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))
