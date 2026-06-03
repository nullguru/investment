# -*- coding: utf-8 -*-
"""
Custom formula lens engine.

A custom lens is a user-defined expression like:
  "ROCE > 15 AND debt_to_equity < 0.3 AND promoter_holding > 40"
  or a weighted score like:
  "roe * 0.4 + fcf_conversion * 0.3 + (1 - debt_to_equity) * 0.3"

Expressions are evaluated against a flat dict of per-symbol metrics
(merged from quality cache, sharia cache, and yfinance section data).

Storage: db/lenses/custom.json

Security: uses a sandboxed eval with a whitelist of allowed names.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import DB_DIR

CUSTOM_PATH = DB_DIR / "lenses" / "custom.json"

# Fields available in custom expressions (from quality cache + sharia + market section)
AVAILABLE_FIELDS = [
    # Quality cache
    "total_score", "roe", "roa", "operating_margin", "gross_margin", "net_margin",
    "ebitda_margin", "revenue_growth", "earnings_growth", "fcf_conversion",
    "debt_to_equity", "current_ratio", "quick_ratio", "interest_coverage",
    "peg_ratio", "trailing_pe", "forward_pe", "price_to_book", "ev_to_ebitda",
    "price_to_sales", "beta", "dividend_yield", "vs_200dma",
    # Sharia cache
    "debt_to_equity_ratio", "cash_to_assets_pct", "other_revenue_to_revenue_pct",
    "receivables_to_assets_pct",
    # Screen pct scores
    "piotroski_pct", "altman_z_pct", "beneish_m_pct", "magic_formula_pct",
    "graham_number_pct", "momentum_pct", "red_flags_pct",
]

_SAFE_NAMES = {
    "abs": abs, "min": min, "max": max, "round": round,
    "sqrt": math.sqrt, "log": math.log, "exp": math.exp,
    "True": True, "False": False, "None": None,
}


def load_custom_lenses() -> list[dict]:
    if not CUSTOM_PATH.exists():
        return []
    try:
        return json.loads(CUSTOM_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(lenses: list[dict]) -> None:
    CUSTOM_PATH.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_PATH.write_text(json.dumps(lenses, indent=2), encoding="utf-8")


def save_custom_lens(lens: dict) -> dict:
    lenses = load_custom_lenses()
    if not lens.get("id"):
        lens["id"] = str(uuid.uuid4())[:8]
    lens.setdefault("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    lens["updated_at"] = datetime.now(timezone.utc).isoformat()
    lens.setdefault("type", "filter")  # "filter" (bool) | "score" (0-100)

    idx = next((i for i, l in enumerate(lenses) if l["id"] == lens["id"]), None)
    if idx is not None:
        lenses[idx] = lens
    else:
        lenses.append(lens)

    _save(lenses)
    return lens


def delete_custom_lens(lens_id: str) -> bool:
    lenses = load_custom_lenses()
    before = len(lenses)
    lenses = [l for l in lenses if l["id"] != lens_id]
    if len(lenses) < before:
        _save(lenses)
        return True
    return False


def _build_context(symbol: str) -> dict[str, Any]:
    """Build the evaluation context (flat metrics dict) for a symbol."""
    from modules.quality import load_quality_cache
    from modules.screener.cache import load_screen_cache
    from modules.sharia import load_cached_sharia

    ctx: dict[str, Any] = {k: None for k in AVAILABLE_FIELDS}

    # Quality cache
    try:
        qc = load_quality_cache().get(symbol, {})
        for k in AVAILABLE_FIELDS:
            if k in qc and qc[k] is not None:
                ctx[k] = qc[k]
    except Exception:
        pass

    # Screen pct scores
    screen_map = {
        "piotroski": "piotroski_pct", "altman_z": "altman_z_pct",
        "beneish_m": "beneish_m_pct", "magic_formula": "magic_formula_pct",
        "graham_number": "graham_number_pct", "momentum": "momentum_pct",
        "red_flags": "red_flags_pct",
    }
    for screen_name, ctx_key in screen_map.items():
        try:
            c = load_screen_cache(screen_name)
            row = c.get(symbol)
            if row:
                ctx[ctx_key] = row.get("pct")
        except Exception:
            pass

    # Sharia cache
    try:
        df = load_cached_sharia("india")
        if df is not None:
            rows = df[df["symbol"] == symbol]
            if not rows.empty:
                row = rows.sort_values("report_period").iloc[-1].to_dict()
                for k in ["debt_to_equity_ratio", "cash_to_assets_pct",
                           "other_revenue_to_revenue_pct", "receivables_to_assets_pct"]:
                    if row.get(k) is not None:
                        ctx[k] = row[k]
    except Exception:
        pass

    # Replace None with 0 for safe arithmetic (but keep flag)
    return ctx


def evaluate_custom_lens(lens: dict, symbol: str) -> dict:
    """
    Evaluate a custom lens expression for symbol.
    Returns {passed, score, value, error, context_fields_used}
    """
    expr = lens.get("expression", "")
    lens_type = lens.get("type", "filter")

    if not expr:
        return {"passed": None, "score": None, "value": None, "error": "No expression defined"}

    ctx = _build_context(symbol)

    # Replace None values with 0 for arithmetic safety
    eval_ctx = {k: (v if v is not None else 0) for k, v in ctx.items()}
    eval_ctx.update(_SAFE_NAMES)

    try:
        result = eval(expr, {"__builtins__": {}}, eval_ctx)  # noqa: S307
    except Exception as e:
        return {"passed": None, "score": None, "value": None, "error": str(e)}

    if lens_type == "filter":
        passed = bool(result)
        return {"passed": passed, "score": 100.0 if passed else 0.0,
                "value": result, "error": None}
    else:
        # Score type: result should be 0-100
        score = max(0.0, min(100.0, float(result)))
        return {"passed": score >= 50, "score": round(score, 1),
                "value": result, "error": None}
