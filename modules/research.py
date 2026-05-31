# -*- coding: utf-8 -*-
"""
Research module: load/save web-researched per-stock analysis.

Storage: one JSON file per symbol in db/research/<SYMBOL>.json
Each file is a dict keyed by section name, each value is an envelope:
  {section, symbol, updated_at, sources: [{title, url}], data: {...}}
"""

from __future__ import annotations

import json
from pathlib import Path

from core.config import DB_DIR

RESEARCH_SECTIONS = [
    "thesis", "industry", "business", "management",
    "esg", "estimates", "revenue", "catalysts",
]

RESEARCH_DIR = DB_DIR / "research"


def _symbol_filename(symbol: str) -> Path:
    """Convert symbol to filename: CUMMINSIND.NS -> CUMMINSIND_NS.json"""
    return RESEARCH_DIR / (symbol.replace(".", "_") + ".json")


def load_research(symbol: str, section: str | None = None) -> dict | None:
    """Load all research or a single section for a symbol.

    Returns the full dict (keyed by section) or a single envelope, or None.
    """
    fp = _symbol_filename(symbol)
    if not fp.exists():
        return None
    data = json.loads(fp.read_text(encoding="utf-8"))
    if section:
        return data.get(section)
    return data


def save_research_section(symbol: str, section: str, envelope: dict) -> None:
    """Merge a section envelope into the symbol's research file."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    fp = _symbol_filename(symbol)
    existing = {}
    if fp.exists():
        existing = json.loads(fp.read_text(encoding="utf-8"))
    existing[section] = envelope
    fp.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
