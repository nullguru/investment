# -*- coding: utf-8 -*-
"""
Per-stock scorecard assembler.

Pulls together all lens types for a single symbol into a unified scorecard:
  - Composite dimensions (Financial Quality, Safety, Governance, etc.)
  - Custom formula lenses
  - Thematic tags
  - Individual quantitative screen scores (raw)
  - Composite score (weighted average of active composite dimensions)
"""

from __future__ import annotations

import math


def compute_scorecard(symbol: str, market: str = "india") -> dict:
    """
    Assemble full scorecard for symbol.

    Returns a dict with:
      composite_dimensions: list of scored composite lenses
      custom_lenses: list of custom lens evaluations
      thematic_tags: list of thematic lens names this symbol belongs to
      raw_screens: dict of individual quantitative screen results
      composite_score: weighted average of available composite dimension scores
      composite_label, composite_color
    """
    from modules.lenses.composite import load_composite_lenses, compute_composite_score, compute_governance_score
    from modules.lenses.thematic import get_symbol_themes
    from modules.lenses.custom import load_custom_lenses, evaluate_custom_lens
    from modules.screener.cache import load_screen_cache
    from modules.quality import load_quality_cache

    sym = symbol.upper()

    # ── 1. Composite dimensions ──────────────────────────────────────────────
    composite_results = []
    for lens in load_composite_lenses():
        if not lens.get("active", True):
            continue
        if lens["id"] == "corporate_governance":
            result = compute_governance_score(sym)
        else:
            result = compute_composite_score(lens, sym)
        if result:
            composite_results.append(result)

    # ── 2. Custom lenses ─────────────────────────────────────────────────────
    custom_results = []
    for lens in load_custom_lenses():
        if not lens.get("active", True):
            continue
        result = evaluate_custom_lens(lens, sym)
        custom_results.append({
            "id": lens["id"],
            "name": lens["name"],
            "emoji": lens.get("emoji", "🔧"),
            "type": lens.get("type", "filter"),
            "expression": lens.get("expression", ""),
            "source": lens.get("source", ""),
            **result,
        })

    # ── 3. Thematic tags ─────────────────────────────────────────────────────
    themes = get_symbol_themes(sym)
    thematic_tags = [{"id": t["id"], "name": t["name"], "emoji": t.get("emoji", "🏷️")} for t in themes]

    # ── 4. Raw screen scores ─────────────────────────────────────────────────
    raw_screens = {}
    for screen_name in ["piotroski", "altman_z", "beneish_m", "magic_formula", "graham_number", "momentum", "red_flags"]:
        try:
            cache = load_screen_cache(screen_name)
            if sym in cache:
                row = cache[sym]
                raw_screens[screen_name] = {
                    "score": row.get("score"),
                    "max_score": row.get("max_score"),
                    "pct": row.get("pct"),
                    "label": row.get("label"),
                    "passed": row.get("passed"),
                }
        except Exception:
            pass

    # Quality score
    try:
        qc = load_quality_cache().get(sym)
        if qc:
            raw_screens["quality"] = {
                "score": qc.get("total_score"),
                "max_score": 100,
                "pct": qc.get("total_score"),
                "label": qc.get("label"),
                "passed": (qc.get("total_score") or 0) >= 65,
            }
    except Exception:
        pass

    # ── 5. Composite overall score ───────────────────────────────────────────
    # Equal-weight all composite dimensions that have data
    scored = [r for r in composite_results if r.get("score") is not None]
    if scored:
        avg = sum(r["score"] for r in scored) / len(scored)
        overall_score = round(avg, 1)
        overall_label, overall_color = _overall_label(overall_score)
    else:
        overall_score = None
        overall_label = "No data"
        overall_color = "slate"

    return {
        "symbol": sym,
        "composite_score": overall_score,
        "composite_label": overall_label,
        "composite_color": overall_color,
        "dimensions_scored": len(scored),
        "dimensions_total": len(composite_results),
        "composite_dimensions": composite_results,
        "custom_lenses": custom_results,
        "thematic_tags": thematic_tags,
        "raw_screens": raw_screens,
    }


def _overall_label(score: float) -> tuple[str, str]:
    if score >= 80: return "Exceptional", "emerald"
    if score >= 65: return "Good", "teal"
    if score >= 50: return "Fair", "amber"
    if score >= 35: return "Weak", "orange"
    return "Poor", "red"
