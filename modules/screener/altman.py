# -*- coding: utf-8 -*-
"""
Altman Z-Score: 5-variable bankruptcy risk prediction model.

Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 0.99×X5

X1 = Working Capital / Total Assets         (liquidity)
X2 = Retained Earnings / Total Assets       (cumulative profitability)
X3 = EBIT / Total Assets                    (operating efficiency)
X4 = Market Cap / Book Value of Total Liabilities  (solvency)
X5 = Revenue / Total Assets                 (asset efficiency)

Zones: Z > 3.0 = Safe, 1.8-3.0 = Gray, < 1.8 = Distress (high bankruptcy risk within 2 years)
"""

from __future__ import annotations

from .base import ScreenResult, safe_float, df_get, get_ticker, insufficient_result

SCREEN_NAME = "altman_z"
PASS_THRESHOLD = 1.8   # below this = distress zone


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

    # Extract components
    ta = df_get(bal, ["Total Assets"], 0) if bal is not None and not bal.empty else None
    ca = df_get(bal, ["Current Assets", "Total Current Assets"], 0) if bal is not None else None
    cl = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 0) if bal is not None else None
    re = df_get(bal, ["Retained Earnings", "Retained Earnings (Deficit)"], 0) if bal is not None else None
    total_liab = df_get(bal, ["Total Liabilities Net Minority Interest", "Total Liabilities", "Total Liab"], 0) if bal is not None else None
    revenue = df_get(inc, ["Total Revenue", "Revenue"], 0) if inc is not None and not inc.empty else None
    ebit = df_get(inc, ["EBIT", "Operating Income", "Ebit"], 0) if inc is not None else None

    # From info
    market_cap = safe_float(info.get("marketCap"))
    if ta is None:
        ta = safe_float(info.get("totalAssets"))
    if revenue is None:
        revenue = safe_float(info.get("totalRevenue"))
    if re is None:
        re = safe_float(info.get("retainedEarnings"))

    # Book value of liabilities fallback
    if total_liab is None and ta is not None:
        total_equity = safe_float(info.get("totalStockholderEquity") or info.get("bookValue"))
        if total_equity is not None and market_cap is not None:
            shares = safe_float(info.get("sharesOutstanding"))
            if shares and shares > 0:
                bvps = total_equity / shares if isinstance(total_equity, float) and total_equity > 1000 else total_equity
                total_liab = ta - (bvps * shares if bvps < 10000 else bvps)

    if ta is None or ta == 0:
        r = insufficient_result(SCREEN_NAME, symbol, "Total assets unavailable")
        cache_result(r.to_dict())
        return r

    wc = (ca - cl) if (ca is not None and cl is not None) else None
    x1 = (wc / ta) if wc is not None else None
    x2 = (re / ta) if re is not None else None
    x3 = (ebit / ta) if ebit is not None else None
    x4 = (market_cap / total_liab) if (market_cap is not None and total_liab and total_liab != 0) else None
    x5 = (revenue / ta) if revenue is not None else None

    available = sum(1 for v in [x1, x2, x3, x4, x5] if v is not None)
    if available < 3:
        r = insufficient_result(SCREEN_NAME, symbol, f"Only {available}/5 components available")
        cache_result(r.to_dict())
        return r

    # Use 0 for missing components (neutral)
    z = (
        1.2 * (x1 or 0) +
        1.4 * (x2 or 0) +
        3.3 * (x3 or 0) +
        0.6 * (x4 or 0) +
        0.99 * (x5 or 0)
    )

    if z > 3.0:    zone, label = "safe",   "Safe"
    elif z > 1.8:  zone, label = "gray",   "Gray Zone"
    else:          zone, label = "distress", "Distress"

    data_quality = "full" if available == 5 else "partial"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=round(z, 3),
        max_score=8.0,
        pct=round(min(z / 8.0 * 100, 100), 1),
        label=label,
        passed=z >= PASS_THRESHOLD,
        breakdown={
            "z_score": round(z, 3),
            "zone": zone,
            "x1_working_capital_ratio": round(x1, 4) if x1 is not None else None,
            "x2_retained_earnings_ratio": round(x2, 4) if x2 is not None else None,
            "x3_ebit_ratio": round(x3, 4) if x3 is not None else None,
            "x4_market_to_liabilities": round(x4, 4) if x4 is not None else None,
            "x5_asset_turnover": round(x5, 4) if x5 is not None else None,
            "components_available": available,
        },
        data_quality=data_quality,
    )
    cache_result(r.to_dict())
    return r
