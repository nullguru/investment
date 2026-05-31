# -*- coding: utf-8 -*-
"""
Quality scoring engine for stock picking.

Scores each stock on 4 dimensions (0-25 each, total 0-100):
  1. Profitability  — ROE, operating margin, gross margin
  2. Cash Generation — FCF/NetIncome conversion, FCF positive
  3. Financial Strength — debt/equity, current ratio
  4. Valuation — PEG ratio (primary), P/E fallback

Labels: Exceptional (80-100), Good (65-79), Fair (50-64), Weak (35-49), Poor (<35)

Data sources:
  - yfinance financials/valuation via modules.market.get_section_data
  - Sharia cache (reuses already-computed debt_to_equity_ratio)
"""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import DB_DIR

QUALITY_CACHE_PATH = DB_DIR / "quality_scores.json"


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def load_quality_cache() -> dict:
    """Load all cached quality scores. Returns {symbol: score_dict}."""
    if not QUALITY_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(QUALITY_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_quality_cache(new_scores: dict) -> None:
    """Merge new_scores into existing cache and persist."""
    existing = load_quality_cache()
    existing.update(new_scores)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_CACHE_PATH.write_text(
        json.dumps(existing, indent=2, default=str), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _safe(v: Any) -> float | None:
    """Return float or None; discard NaN/Inf."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def score_profitability(fin: dict) -> dict:
    """ROE (0-10) + operating margin (0-10) + gross margin (0-5) = max 25."""
    roe = _safe(fin.get("returnOnEquity"))
    op_margin = _safe(fin.get("operatingMargins"))
    gross_margin = _safe(fin.get("grossMargins"))

    roe_pts = 0
    if roe is not None:
        if roe > 0.25:   roe_pts = 10
        elif roe > 0.15: roe_pts = 7
        elif roe > 0.10: roe_pts = 4

    op_pts = 0
    if op_margin is not None:
        if op_margin > 0.20:   op_pts = 10
        elif op_margin > 0.15: op_pts = 6
        elif op_margin > 0.10: op_pts = 3

    gm_pts = 0
    if gross_margin is not None:
        if gross_margin > 0.40:   gm_pts = 5
        elif gross_margin > 0.30: gm_pts = 3

    score = roe_pts + op_pts + gm_pts
    metrics_available = sum(1 for v in [roe, op_margin, gross_margin] if v is not None)
    return {
        "score": score,
        "max": 25,
        "roe": roe,
        "operating_margin": op_margin,
        "gross_margin": gross_margin,
        "metrics_available": metrics_available,
    }


def score_cash_generation(fin: dict) -> dict:
    """FCF/NetIncome conversion (0-20) + FCF positive (0-5) = max 25."""
    fcf = _safe(fin.get("freeCashFlow"))
    net_income = _safe(fin.get("netIncome"))

    fcf_positive_pts = 5 if (fcf is not None and fcf > 0) else 0

    conversion = None
    conv_pts = 0
    if fcf is not None and net_income is not None and net_income != 0:
        conversion = fcf / net_income
        if conversion > 0.80:   conv_pts = 20
        elif conversion > 0.50: conv_pts = 13
        elif conversion > 0.20: conv_pts = 7

    score = conv_pts + fcf_positive_pts
    metrics_available = sum(1 for v in [fcf, net_income] if v is not None)
    return {
        "score": score,
        "max": 25,
        "fcf": fcf,
        "net_income": net_income,
        "fcf_conversion": conversion,
        "fcf_positive": fcf is not None and fcf > 0,
        "metrics_available": metrics_available,
    }


def score_financial_strength(fin: dict, sharia_row: dict | None = None) -> dict:
    """Debt/equity (0-15) + current ratio (0-10) = max 25."""
    # Prefer Sharia cache D/E (already computed per period) over yfinance
    de = None
    if sharia_row:
        de = _safe(sharia_row.get("debt_to_equity_ratio"))
    if de is None:
        de = _safe(fin.get("debtToEquity"))
        if de is not None:
            de = de / 100.0  # yfinance gives it as percentage (e.g. 10.38 = 10.38%)

    current_ratio = _safe(fin.get("currentRatio"))

    de_pts = 0
    if de is not None:
        if de < 0.10:   de_pts = 15
        elif de < 0.33: de_pts = 8

    cr_pts = 0
    if current_ratio is not None:
        if current_ratio > 2.0:   cr_pts = 10
        elif current_ratio > 1.5: cr_pts = 6
        elif current_ratio > 1.0: cr_pts = 3

    score = de_pts + cr_pts
    metrics_available = sum(1 for v in [de, current_ratio] if v is not None)
    return {
        "score": score,
        "max": 25,
        "debt_to_equity": de,
        "current_ratio": current_ratio,
        "metrics_available": metrics_available,
    }


def score_valuation(val: dict) -> dict:
    """PEG ratio (0-25). Falls back to forward P/E heuristic if PEG unavailable."""
    peg = _safe(val.get("pegRatio"))
    trailing_pe = _safe(val.get("trailingPE"))
    forward_pe = _safe(val.get("forwardPE"))

    peg_pts = 0
    used_metric = "peg"
    if peg is not None and peg > 0:
        if peg < 1.0:   peg_pts = 25
        elif peg < 1.5: peg_pts = 20
        elif peg < 2.0: peg_pts = 13
        elif peg < 3.0: peg_pts = 6
    elif forward_pe is not None and forward_pe > 0:
        # Heuristic: forward P/E as rough valuation proxy
        used_metric = "forward_pe"
        if forward_pe < 12:   peg_pts = 20
        elif forward_pe < 18: peg_pts = 15
        elif forward_pe < 25: peg_pts = 10
        elif forward_pe < 35: peg_pts = 5
    elif trailing_pe is not None and trailing_pe > 0:
        used_metric = "trailing_pe"
        if trailing_pe < 15:   peg_pts = 18
        elif trailing_pe < 22: peg_pts = 13
        elif trailing_pe < 30: peg_pts = 8
        elif trailing_pe < 40: peg_pts = 4
    else:
        # No valuation data — neutral mid score
        peg_pts = 12
        used_metric = "none"

    metrics_available = sum(1 for v in [peg, trailing_pe, forward_pe] if v is not None)
    return {
        "score": peg_pts,
        "max": 25,
        "peg_ratio": peg,
        "trailing_pe": trailing_pe,
        "forward_pe": forward_pe,
        "used_metric": used_metric,
        "metrics_available": metrics_available,
    }


def _quality_label(total: int) -> str:
    if total >= 80: return "Exceptional"
    if total >= 65: return "Good"
    if total >= 50: return "Fair"
    if total >= 35: return "Weak"
    return "Poor"


# ---------------------------------------------------------------------------
# Main compute
# ---------------------------------------------------------------------------

def compute_quality_score(
    symbol: str,
    force: bool = False,
    sharia_row: dict | None = None,
    market: str = "india",
) -> dict:
    """
    Fetch financials + valuation for symbol, score all 4 dimensions.

    Returns a score dict suitable for caching and API responses.
    Uses in-memory yfinance cache (modules.market) unless force=True.
    market: 'india' (default) or 'us' — controls ticker suffix handling.
    """
    from modules.market import get_section_data

    # Check disk cache first (unless force)
    if not force:
        cache = load_quality_cache()
        if symbol in cache:
            return cache[symbol]

    fin = get_section_data(symbol, "financials", force=force, market=market)
    val = get_section_data(symbol, "valuation", force=force, market=market)

    if fin.get("error") or val.get("error"):
        result = {
            "symbol": symbol,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "total_score": None,
            "label": None,
            "error": fin.get("error") or val.get("error"),
            "data_quality": "insufficient",
        }
        save_quality_cache({symbol: result})
        return result

    p = score_profitability(fin)
    c = score_cash_generation(fin)
    f = score_financial_strength(fin, sharia_row=sharia_row)
    v = score_valuation(val)

    total = p["score"] + c["score"] + f["score"] + v["score"]

    # Data quality assessment
    total_metrics = p["metrics_available"] + c["metrics_available"] + f["metrics_available"] + v["metrics_available"]
    if total_metrics >= 7:
        data_quality = "full"
    elif total_metrics >= 4:
        data_quality = "partial"
    else:
        data_quality = "insufficient"

    result = {
        "symbol": symbol,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "total_score": total,
        "label": _quality_label(total),
        "data_quality": data_quality,
        "profitability": p,
        "cash_generation": c,
        "financial_strength": f,
        "valuation": v,
        # Flat copies of key metrics for screener table joins
        "profitability_score": p["score"],
        "cash_generation_score": c["score"],
        "financial_strength_score": f["score"],
        "valuation_score": v["score"],
        "roe": p["roe"],
        "operating_margin": p["operating_margin"],
        "gross_margin": p["gross_margin"],
        "fcf_conversion": c["fcf_conversion"],
        "debt_to_equity": f["debt_to_equity"],
        "current_ratio": f["current_ratio"],
        "peg_ratio": v["peg_ratio"],
        "trailing_pe": v["trailing_pe"],
        "forward_pe": v["forward_pe"],
    }

    save_quality_cache({symbol: result})
    return result


def batch_compute_quality(
    symbols: list[str],
    workers: int = 5,
    force: bool = False,
    sharia_rows: dict | None = None,
    progress_cb=None,
    market: str = "india",
) -> list[dict]:
    """
    Parallel quality score computation for a list of symbols.

    Args:
        symbols: list of ticker strings
        workers: thread pool size (default 5 — yfinance rate-limit friendly)
        force: bypass disk cache
        sharia_rows: optional {symbol: sharia_row_dict} to enrich financial_strength scoring
        progress_cb: optional callable(done, total) for progress reporting
        market: 'india' (default) or 'us'

    Returns list of score dicts in input order.
    """
    results: dict[str, dict] = {}
    sharia_rows = sharia_rows or {}
    total = len(symbols)

    def _compute_one(sym: str) -> tuple[str, dict]:
        row = sharia_rows.get(sym)
        return sym, compute_quality_score(sym, force=force, sharia_row=row, market=market)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_compute_one, sym): sym for sym in symbols}
        for fut in as_completed(futures):
            sym, score = fut.result()
            results[sym] = score
            done += 1
            if progress_cb:
                progress_cb(done, total)

    return [results[sym] for sym in symbols if sym in results]
