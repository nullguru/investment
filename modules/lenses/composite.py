# -*- coding: utf-8 -*-
"""
Composite lens engine.

Composite lenses combine multiple quantitative screen scores (from
modules/screener caches) using user-defined weights into a single 0-100
dimension score. E.g. "Financial Quality" = 45% Quality + 35% Piotroski + 20% Red Flags (inverted).

Definitions live in db/lenses/composite.json and are fully editable.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import DB_DIR

COMPOSITE_PATH = DB_DIR / "lenses" / "composite.json"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_composite_lenses() -> list[dict]:
    """Load all composite lens definitions."""
    if not COMPOSITE_PATH.exists():
        return []
    try:
        return json.loads(COMPOSITE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_composite_lens(lens: dict) -> dict:
    """Upsert a composite lens by id. Creates id if missing."""
    lenses = load_composite_lenses()
    if not lens.get("id"):
        lens["id"] = str(uuid.uuid4())[:8]
    lens.setdefault("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    lens["updated_at"] = datetime.now(timezone.utc).isoformat()

    idx = next((i for i, l in enumerate(lenses) if l["id"] == lens["id"]), None)
    if idx is not None:
        lenses[idx] = lens
    else:
        lenses.append(lens)

    COMPOSITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPOSITE_PATH.write_text(json.dumps(lenses, indent=2), encoding="utf-8")
    return lens


def delete_composite_lens(lens_id: str) -> bool:
    lenses = load_composite_lenses()
    before = len(lenses)
    lenses = [l for l in lenses if l["id"] != lens_id]
    if len(lenses) < before:
        COMPOSITE_PATH.write_text(json.dumps(lenses, indent=2), encoding="utf-8")
        return True
    return False


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _safe(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _threshold_label(score: float, thresholds: list[dict]) -> dict:
    """Return the matching threshold dict for a score."""
    for t in sorted(thresholds, key=lambda x: x["min"], reverse=True):
        if score >= t["min"]:
            return t
    return thresholds[-1] if thresholds else {"label": "—", "color": "slate"}


def compute_composite_score(lens: dict, symbol: str) -> dict:
    """
    Compute a composite score for symbol given a lens definition.

    Returns:
      {score, label, color, components: [{screen, weight, raw_pct, contribution, available}], coverage_pct}
    """
    from modules.screener.cache import load_screen_cache
    from modules.quality import load_quality_cache

    components_out = []
    weighted_sum = 0.0
    total_weight = 0.0

    for comp in lens.get("components", []):
        screen = comp["screen"]
        field  = comp.get("field", "pct")
        weight = float(comp.get("weight", 0))
        invert = bool(comp.get("invert", False))

        raw_pct = None
        try:
            if screen == "quality":
                cache = load_quality_cache()
                row = cache.get(symbol)
                if row:
                    raw_pct = _safe(row.get("total_score"))
            else:
                cache = load_screen_cache(screen)
                row = cache.get(symbol)
                if row:
                    raw_pct = _safe(row.get(field))
        except Exception:
            pass

        available = raw_pct is not None
        contribution = None

        if available:
            val = 100.0 - raw_pct if invert else raw_pct
            val = max(0.0, min(100.0, val))
            contribution = val * weight
            weighted_sum += contribution
            total_weight += weight

        components_out.append({
            "screen": screen,
            "weight": weight,
            "raw_pct": round(raw_pct, 1) if raw_pct is not None else None,
            "effective_pct": round(100.0 - raw_pct if (invert and raw_pct is not None) else (raw_pct or 0), 1),
            "contribution": round(contribution, 2) if contribution is not None else None,
            "available": available,
            "invert": invert,
            "note": comp.get("note", ""),
        })

    # Normalise by available weight only
    if total_weight == 0:
        return {
            "lens_id": lens["id"],
            "lens_name": lens["name"],
            "score": None,
            "label": "No data",
            "color": "slate",
            "coverage_pct": 0,
            "components": components_out,
        }

    # Scale to full weight if some components missing
    total_defined_weight = sum(c["weight"] for c in lens.get("components", []))
    score = (weighted_sum / total_weight) * 1.0  # already 0-100
    coverage = round(total_weight / total_defined_weight * 100) if total_defined_weight else 0

    threshold = _threshold_label(score, lens.get("thresholds", []))

    return {
        "lens_id": lens["id"],
        "lens_name": lens["name"],
        "emoji": lens.get("emoji", ""),
        "score": round(score, 1),
        "label": threshold["label"],
        "color": threshold["color"],
        "coverage_pct": coverage,
        "components": components_out,
    }


def compute_governance_score(symbol: str) -> dict | None:
    """
    Compute corporate governance score from field gaps data + AI research.
    Returns {score, label, color, signals: [...], coverage_pct} or None.
    """
    from modules.market.field_gaps import get_symbol_gaps
    from modules.market import get_section_data
    from modules.research import load_research

    signals = []
    weighted_sum = 0.0
    total_weight = 0.0

    lenses = load_composite_lenses()
    gov = next((l for l in lenses if l["id"] == "corporate_governance"), None)
    if not gov:
        return None

    for qf in gov.get("qualitative_fields", []):
        field   = qf["field"]
        weight  = float(qf.get("weight", 0))
        section = qf.get("section", "overview")

        val = None
        source = None

        if section == "research" and field == "forensic_score":
            # Pull from AI research forensic section
            try:
                research = load_research(symbol)
                if research and "forensic" in research:
                    forensic = research["forensic"]
                    # Look for governance_score or forensic_score sub-field
                    val = _safe(forensic.get("governance_score") or forensic.get("forensic_score"))
                    if val is not None:
                        val = val * 10  # 0-10 → 0-100
                        source = "ai_research"
            except Exception:
                pass
        else:
            # Try yfinance section data
            try:
                data = get_section_data(symbol, section)
                raw = data.get(field)
                if raw is not None:
                    val = _safe(raw)
                    source = "yfinance"
            except Exception:
                pass

        if val is None:
            signals.append({"field": field, "weight": weight, "value": None, "score": None,
                            "source": None, "note": qf.get("note", ""), "ai_needed": True})
            continue

        # Score the field
        pts = 0.0
        if "good_below" in qf:
            good_below = qf["good_below"]
            bad_above  = qf.get("bad_above", good_below * 3)
            if val <= good_below:
                pts = 100.0
            elif val >= bad_above:
                pts = 0.0
            else:
                pts = 100.0 * (1 - (val - good_below) / (bad_above - good_below))
        elif "good_above" in qf:
            good_above = qf["good_above"]
            bad_below  = qf.get("bad_below", good_above / 2)
            if val >= good_above:
                pts = 100.0
            elif val <= bad_below:
                pts = 0.0
            else:
                pts = 100.0 * (val - bad_below) / (good_above - bad_below)
        else:
            pts = max(0.0, min(100.0, val))

        weighted_sum += pts * weight
        total_weight += weight

        signals.append({"field": field, "weight": weight, "value": round(val, 2),
                        "score": round(pts, 1), "source": source,
                        "note": qf.get("note", ""), "ai_needed": source == "ai_research" or source is None})

    if total_weight == 0:
        return {
            "lens_id": "corporate_governance",
            "lens_name": "Corporate Governance",
            "emoji": "🏛️",
            "score": None,
            "label": "Needs AI research",
            "color": "slate",
            "coverage_pct": 0,
            "signals": signals,
            "components": [],
        }

    total_defined = sum(qf.get("weight", 0) for qf in gov.get("qualitative_fields", []))
    score = weighted_sum / total_weight
    coverage = round(total_weight / total_defined * 100) if total_defined else 0
    threshold = _threshold_label(score, gov.get("thresholds", []))

    return {
        "lens_id": "corporate_governance",
        "lens_name": "Corporate Governance",
        "emoji": "🏛️",
        "score": round(score, 1),
        "label": threshold["label"],
        "color": threshold["color"],
        "coverage_pct": coverage,
        "signals": signals,
        "components": [],
    }
