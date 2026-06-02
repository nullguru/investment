# -*- coding: utf-8 -*-
"""
Research module: load/save web-researched per-stock analysis.

Storage: one JSON file per symbol in db/research/<SYMBOL>.json
Each file is a dict keyed by section name.

New versioned format (v2):
  {
    "thesis": {
      "current": {section, symbol, updated_at, sources, data},
      "versions": [   # oldest → newest-before-current
        {section, symbol, updated_at, sources, data},
        ...
      ]
    }
  }

Legacy flat format (v1) is read transparently; migrated to v2 on first write.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.config import DB_DIR

RESEARCH_SECTIONS = [
    # Research (AI) — core sections
    "thesis", "industry", "business", "management",
    "esg", "estimates", "revenue", "catalysts", "cyclical",
    # More (AI) — extended sections
    "ma", "value", "faq", "credit", "geofx", "capital",
    "forensic", "iprd", "supply_chain",
]

RESEARCH_DIR = DB_DIR / "research"
MAX_VERSIONS = 20  # keep at most this many historical versions per section


def _symbol_filename(symbol: str) -> Path:
    """Convert symbol to filename: CUMMINSIND.NS -> CUMMINSIND_NS.json"""
    return RESEARCH_DIR / (symbol.replace(".", "_") + ".json")


def _is_versioned(entry: dict) -> bool:
    """True if the entry is in the new versioned format."""
    return isinstance(entry, dict) and "current" in entry


def _to_envelope(entry: dict) -> dict | None:
    """Extract the current envelope from either v1 (flat) or v2 (versioned) entry."""
    if entry is None:
        return None
    if _is_versioned(entry):
        return entry.get("current")
    # v1 flat envelope — return as-is
    return entry


def load_research(symbol: str, section: str | None = None) -> dict | None:
    """Load all research or a single section for a symbol.

    Always returns plain envelopes (not versioned wrappers), for backward compat.
    Returns the full dict (keyed by section → envelope) or a single envelope, or None.
    """
    fp = _symbol_filename(symbol)
    if not fp.exists():
        return None
    data = json.loads(fp.read_text(encoding="utf-8"))
    if section:
        entry = data.get(section)
        return _to_envelope(entry)
    # Return flat dict of section → current envelope
    return {k: _to_envelope(v) for k, v in data.items()}


def load_research_versions(symbol: str, section: str) -> list[dict]:
    """Return historical versions for a section (newest first, not including current).

    Each item is an envelope dict with at least `updated_at`.
    """
    fp = _symbol_filename(symbol)
    if not fp.exists():
        return []
    data = json.loads(fp.read_text(encoding="utf-8"))
    entry = data.get(section)
    if not entry:
        return []
    if _is_versioned(entry):
        versions = entry.get("versions") or []
        # Return newest first (reverse of storage order)
        return list(reversed(versions))
    # v1 flat — no history
    return []


def save_research_section(symbol: str, section: str, envelope: dict) -> None:
    """Merge a new section envelope into the symbol's research file, versioning the old one."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    fp = _symbol_filename(symbol)
    existing: dict = {}
    if fp.exists():
        existing = json.loads(fp.read_text(encoding="utf-8"))

    entry = existing.get(section)
    old_versions: list[dict] = []
    old_current: dict | None = None

    if entry is not None:
        if _is_versioned(entry):
            old_current = entry.get("current")
            old_versions = list(entry.get("versions") or [])
        else:
            # v1 flat envelope — promote to versioned
            old_current = entry

    # Push old current into versions (if it exists and has data)
    if old_current and old_current.get("updated_at"):
        old_versions.append(old_current)
        # Trim to max
        if len(old_versions) > MAX_VERSIONS:
            old_versions = old_versions[-MAX_VERSIONS:]

    existing[section] = {
        "current": envelope,
        "versions": old_versions,
    }
    fp.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_research_version(symbol: str, section: str, version_idx: int) -> bool:
    """Delete a historical version by index (0 = newest historical).

    Returns True if deleted, False if not found.
    """
    fp = _symbol_filename(symbol)
    if not fp.exists():
        return False
    data = json.loads(fp.read_text(encoding="utf-8"))
    entry = data.get(section)
    if not entry or not _is_versioned(entry):
        return False
    versions = list(entry.get("versions") or [])
    # Index 0 = newest (reversed), so convert
    reversed_idx = len(versions) - 1 - version_idx
    if reversed_idx < 0 or reversed_idx >= len(versions):
        return False
    versions.pop(reversed_idx)
    data[section]["versions"] = versions
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def restore_research_version(symbol: str, section: str, version_idx: int) -> dict | None:
    """Promote a historical version to current (swaps current ↔ version).

    Returns the restored envelope, or None if not found.
    """
    fp = _symbol_filename(symbol)
    if not fp.exists():
        return None
    data = json.loads(fp.read_text(encoding="utf-8"))
    entry = data.get(section)
    if not entry or not _is_versioned(entry):
        return None
    versions = list(entry.get("versions") or [])
    reversed_idx = len(versions) - 1 - version_idx
    if reversed_idx < 0 or reversed_idx >= len(versions):
        return None
    # Swap
    target = versions.pop(reversed_idx)
    current = entry.get("current")
    if current:
        versions.append(current)
    data[section] = {"current": target, "versions": versions}
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return target
