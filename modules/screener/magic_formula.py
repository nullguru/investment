# -*- coding: utf-8 -*-
"""
Greenblatt Magic Formula: quality businesses at cheap prices.

Two metrics (both should be maximized):
  ROCE (Return on Capital Employed) = EBIT / (Net Working Capital + Net Fixed Assets)
  Earnings Yield                    = EBIT / Enterprise Value

For a single stock, both are scored on absolute thresholds.
For batch ranking, use rank_batch() which computes combined rank.

ROCE > 25% and EY > 8% = strongly attractive
ROCE > 15% and EY > 5% = attractive
"""

from __future__ import annotations

from .base import ScreenResult, safe_float, df_get, get_ticker, insufficient_result

SCREEN_NAME = "magic_formula"
PASS_THRESHOLD = 60.0   # composite score threshold


def compute(symbol: str, force: bool = False, market: str = "india") -> ScreenResult:
    from .cache import get_cached_result, cache_result

    if not force:
        cached = get_cached_result(SCREEN_NAME, symbol)
        if cached:
            return ScreenResult.from_dict(cached)

    try:
        ticker = get_ticker(symbol, market=market)
        info = ticker.info or {}
        inc = ticker.financials
        bal = ticker.balance_sheet
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    # EBIT: try income statement first, then info
    ebit = df_get(inc, ["EBIT", "Operating Income", "Ebit"], 0) if inc is not None and not inc.empty else None
    if ebit is None:
        ebit = safe_float(info.get("ebit") or info.get("operatingIncome"))

    # Enterprise Value
    ev = safe_float(info.get("enterpriseValue"))

    # Working Capital = Current Assets - Current Liabilities
    ca = df_get(bal, ["Current Assets", "Total Current Assets"], 0) if bal is not None and not bal.empty else None
    cl = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 0) if bal is not None else None
    nwc = (ca - cl) if (ca is not None and cl is not None) else None

    # Net Fixed Assets (Net PP&E)
    ppe = df_get(bal, ["Net PPE", "Property Plant And Equipment Net", "Net Property Plant And Equipment"], 0) if bal is not None else None
    if ppe is None:
        ppe = safe_float(info.get("netPPE"))

    invested_capital = None
    if nwc is not None and ppe is not None:
        invested_capital = nwc + ppe
    elif ppe is not None:
        invested_capital = ppe     # fallback: just PP&E

    # Compute metrics
    roce = (ebit / invested_capital) if (ebit is not None and invested_capital and invested_capital > 0) else None
    earnings_yield = (ebit / ev * 100) if (ebit is not None and ev and ev > 0) else None

    available = sum(1 for v in [ebit, ev, nwc, ppe] if v is not None)
    if available < 2 or (roce is None and earnings_yield is None):
        r = insufficient_result(SCREEN_NAME, symbol, "Need EBIT + (EV or invested capital)")
        cache_result(r.to_dict())
        return r

    # Score each metric on absolute thresholds (0-50 each, total 0-100)
    roce_score = 0.0
    if roce is not None:
        if roce > 0.30:   roce_score = 50.0
        elif roce > 0.20: roce_score = 40.0
        elif roce > 0.15: roce_score = 30.0
        elif roce > 0.10: roce_score = 20.0
        elif roce > 0.05: roce_score = 10.0

    ey_score = 0.0
    if earnings_yield is not None:
        if earnings_yield > 12:   ey_score = 50.0
        elif earnings_yield > 8:  ey_score = 40.0
        elif earnings_yield > 6:  ey_score = 30.0
        elif earnings_yield > 4:  ey_score = 20.0
        elif earnings_yield > 2:  ey_score = 10.0

    composite = roce_score + ey_score

    if composite >= 80:    label = "Excellent"
    elif composite >= 60:  label = "Good"
    elif composite >= 40:  label = "Fair"
    else:                  label = "Weak"

    data_quality = "full" if available >= 3 else "partial"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=round(composite, 1),
        max_score=100.0,
        pct=round(composite, 1),
        label=label,
        passed=composite >= PASS_THRESHOLD,
        breakdown={
            "roce_pct": round(roce * 100, 2) if roce is not None else None,
            "earnings_yield_pct": round(earnings_yield, 2) if earnings_yield is not None else None,
            "ebit": ebit,
            "enterprise_value": ev,
            "net_working_capital": nwc,
            "net_ppe": ppe,
            "invested_capital": invested_capital,
            "roce_score": roce_score,
            "ey_score": ey_score,
        },
        data_quality=data_quality,
    )
    cache_result(r.to_dict())
    return r


def rank_batch(symbol_results: list[dict]) -> list[dict]:
    """
    Given a list of magic_formula result dicts (from batch compute),
    add rank columns based on combined ROCE + Earnings Yield ranking.
    Lower combined rank = more attractive.
    """
    import math

    valid = [r for r in symbol_results if r.get("breakdown", {}).get("roce_pct") is not None
             or r.get("breakdown", {}).get("earnings_yield_pct") is not None]

    def _safe(v):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return float(v)

    # Rank by ROCE (higher = better = lower rank number)
    roce_sorted = sorted(valid, key=lambda r: _safe(r["breakdown"].get("roce_pct")), reverse=True)
    roce_ranks = {r["symbol"]: i + 1 for i, r in enumerate(roce_sorted)}

    # Rank by Earnings Yield (higher = better = lower rank number)
    ey_sorted = sorted(valid, key=lambda r: _safe(r["breakdown"].get("earnings_yield_pct")), reverse=True)
    ey_ranks = {r["symbol"]: i + 1 for i, r in enumerate(ey_sorted)}

    for r in symbol_results:
        sym = r["symbol"]
        r_rank = roce_ranks.get(sym, len(valid))
        ey_rank = ey_ranks.get(sym, len(valid))
        combined = r_rank + ey_rank
        r["breakdown"] = r.get("breakdown") or {}
        r["breakdown"]["roce_rank"] = r_rank
        r["breakdown"]["ey_rank"] = ey_rank
        r["breakdown"]["combined_rank"] = combined

    return sorted(symbol_results, key=lambda r: r.get("breakdown", {}).get("combined_rank", 99999))
