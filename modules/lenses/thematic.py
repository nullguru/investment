# -*- coding: utf-8 -*-
"""
Thematic lens management.

A thematic lens is a curated list of symbols grouped by an investment idea
(e.g. "AI Supply Chain India", "China+1 Beneficiaries", "India Grid Infra").

Unlike quantitative screens, thematic membership is manual — you decide
which stocks belong based on reading, research, or conviction.

Storage: db/lenses/thematic.json  →  list of thematic dicts
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.config import DB_DIR

THEMATIC_PATH = DB_DIR / "lenses" / "thematic.json"


def load_thematics() -> list[dict]:
    if not THEMATIC_PATH.exists():
        return []
    try:
        return json.loads(THEMATIC_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(thematics: list[dict]) -> None:
    THEMATIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    THEMATIC_PATH.write_text(json.dumps(thematics, indent=2), encoding="utf-8")


def save_thematic(theme: dict) -> dict:
    """Upsert a thematic lens. Generates id if missing."""
    thematics = load_thematics()
    if not theme.get("id"):
        theme["id"] = str(uuid.uuid4())[:8]
    theme.setdefault("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    theme["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Normalise symbols list
    theme["symbols"] = [s.strip().upper() for s in theme.get("symbols", []) if s.strip()]

    idx = next((i for i, t in enumerate(thematics) if t["id"] == theme["id"]), None)
    if idx is not None:
        thematics[idx] = theme
    else:
        thematics.append(theme)

    _save(thematics)
    return theme


def delete_thematic(theme_id: str) -> bool:
    thematics = load_thematics()
    before = len(thematics)
    thematics = [t for t in thematics if t["id"] != theme_id]
    if len(thematics) < before:
        _save(thematics)
        return True
    return False


def get_symbol_themes(symbol: str) -> list[dict]:
    """Return all thematic lenses that contain this symbol."""
    sym = symbol.upper()
    return [t for t in load_thematics() if sym in [s.upper() for s in t.get("symbols", [])]]
