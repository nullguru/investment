# -*- coding: utf-8 -*-
"""
Ideas inbox — capture raw investment ideas before they're formalized into lenses.

An idea is a half-formed hypothesis: something you read in an article, heard
on a podcast, or noticed in a macro trend. You capture it here so it doesn't
get lost. Later you can promote it to a thematic list or a custom lens.

Storage: db/lenses/ideas.json
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.config import DB_DIR

IDEAS_PATH = DB_DIR / "lenses" / "ideas.json"


def load_ideas() -> list[dict]:
    if not IDEAS_PATH.exists():
        return []
    try:
        data = json.loads(IDEAS_PATH.read_text(encoding="utf-8"))
        return sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
    except (json.JSONDecodeError, OSError):
        return []


def _save(ideas: list[dict]) -> None:
    IDEAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    IDEAS_PATH.write_text(json.dumps(ideas, indent=2), encoding="utf-8")


def save_idea(idea: dict) -> dict:
    """Create or update an idea. Generates id if missing."""
    ideas = load_ideas()
    if not idea.get("id"):
        idea["id"] = str(uuid.uuid4())[:8]
    idea.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    idea.setdefault("status", "raw")          # raw | exploring | promoted | dismissed
    idea.setdefault("source_type", "article") # article | book | podcast | observation | earnings_call
    idea["updated_at"] = datetime.now(timezone.utc).isoformat()

    idx = next((i for i, d in enumerate(ideas) if d["id"] == idea["id"]), None)
    if idx is not None:
        ideas[idx] = idea
    else:
        ideas.insert(0, idea)

    _save(ideas)
    return idea


def update_idea(idea_id: str, updates: dict) -> dict | None:
    ideas = load_ideas()
    for idea in ideas:
        if idea["id"] == idea_id:
            idea.update(updates)
            idea["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(ideas)
            return idea
    return None


def delete_idea(idea_id: str) -> bool:
    ideas = load_ideas()
    before = len(ideas)
    ideas = [i for i in ideas if i["id"] != idea_id]
    if len(ideas) < before:
        _save(ideas)
        return True
    return False
