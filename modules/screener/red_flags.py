# -*- coding: utf-8 -*-
"""
Red Flags screen: composite hard-avoid signal detector.

Counts how many of 8 red flags are triggered. Each flag = 1 point.
  0 = clean (all clear)
  1-2 = caution (investigate before buying)
  3+ = avoid (multiple structural problems)

Flags:
  1. Poor cash conversion: OCF / Net Income < 0.5 (earnings not backed by cash)
  2. High leverage: Debt-to-Equity > 1.0 (more debt than equity)
  3. Negative FCF: Free Cash Flow < 0 (cash burning)
  4. Revenue declining: YoY revenue growth < 0
  5. Gross margin eroding: Gross margin fell >200 bps YoY
  6. Negative working capital: Current Assets < Current Liabilities
  7. Excessive goodwill: Goodwill / Total Assets > 0.3 (intangible-heavy, impairment risk)
  8. Extreme P/E: Trailing P/E > 100 AND revenue growth < 20% (not justified growth premium)
"""

from __future__ import annotations

from .base import ScreenResult, safe_float, df_get, get_ticker, insufficient_result

SCREEN_NAME = "red_flags"
PASS_THRESHOLD = 2.0   # ≤2 flags = caution but acceptable; 3+ = avoid


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
        cf_stmt = ticker.cashflow
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    flags: dict[str, bool] = {}
    available = 0

    # --- Data extraction ---
    ni = df_get(inc, ["Net Income", "Net Income Common Stockholders"], 0) if inc is not None and not inc.empty else None
    ni = ni or safe_float(info.get("netIncomeToCommon"))

    revenue_cur = df_get(inc, ["Total Revenue", "Revenue"], 0) if inc is not None and not inc.empty else None
    revenue_pri = df_get(inc, ["Total Revenue", "Revenue"], 1) if inc is not None and not inc.empty and len(inc.columns) > 1 else None
    if revenue_cur is None:
        revenue_cur = safe_float(info.get("totalRevenue"))

    cogs_cur = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 0) if inc is not None else None
    cogs_pri = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 1) if inc is not None and inc is not None and len(inc.columns if inc is not None else []) > 1 else None

    ta = df_get(bal, ["Total Assets"], 0) if bal is not None and not bal.empty else None
    ta = ta or safe_float(info.get("totalAssets"))

    ca = df_get(bal, ["Current Assets", "Total Current Assets"], 0) if bal is not None else None
    cl = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 0) if bal is not None else None

    goodwill = df_get(bal, ["Goodwill", "Goodwill And Other Intangible Assets"], 0) if bal is not None else None

    ocf = df_get(cf_stmt, ["Operating Cash Flow", "Cash From Operating Activities"], 0) if cf_stmt is not None and not cf_stmt.empty else None
    fcf = safe_float(info.get("freeCashflow"))
    if fcf is None:
        cap_ex = df_get(cf_stmt, ["Capital Expenditure", "Capital Expenditure Reported"], 0) if cf_stmt is not None else None
        if ocf is not None and cap_ex is not None:
            fcf = ocf + cap_ex  # capex in yf is usually negative

    de = safe_float(info.get("debtToEquity"))
    if de is not None and de > 10:
        de = de / 100  # yfinance sometimes returns 35.6 for 0.356

    trailing_pe = safe_float(info.get("trailingPE"))

    # --- Flag 1: Poor cash conversion (OCF / NI < 0.5) ---
    if ocf is not None and ni is not None and ni > 0:
        available += 1
        flags["poor_cash_conversion"] = (ocf / ni) < 0.5
    else:
        flags["poor_cash_conversion"] = False

    # --- Flag 2: High leverage (D/E > 1.0) ---
    if de is not None:
        available += 1
        flags["high_leverage"] = de > 1.0
    else:
        flags["high_leverage"] = False

    # --- Flag 3: Negative FCF ---
    if fcf is not None:
        available += 1
        flags["negative_fcf"] = fcf < 0
    else:
        flags["negative_fcf"] = False

    # --- Flag 4: Revenue declining YoY ---
    if revenue_cur is not None and revenue_pri is not None and revenue_pri > 0:
        available += 1
        flags["revenue_declining"] = revenue_cur < revenue_pri
    else:
        flags["revenue_declining"] = False

    # --- Flag 5: Gross margin eroding >200 bps ---
    if revenue_cur and cogs_cur is not None and revenue_pri and cogs_pri is not None and revenue_cur > 0 and revenue_pri > 0:
        gm_cur = (revenue_cur - cogs_cur) / revenue_cur
        gm_pri = (revenue_pri - cogs_pri) / revenue_pri
        available += 1
        flags["gross_margin_eroding"] = (gm_pri - gm_cur) > 0.02   # > 200 bps decline
    else:
        flags["gross_margin_eroding"] = False

    # --- Flag 6: Negative working capital ---
    if ca is not None and cl is not None:
        available += 1
        flags["negative_working_capital"] = ca < cl
    else:
        flags["negative_working_capital"] = False

    # --- Flag 7: Excessive goodwill (>30% of assets) ---
    if goodwill is not None and ta and ta > 0:
        available += 1
        flags["excessive_goodwill"] = (goodwill / ta) > 0.30
    else:
        flags["excessive_goodwill"] = False

    # --- Flag 8: Unjustified extreme P/E (>100x without growth) ---
    if trailing_pe is not None:
        available += 1
        rev_growth = ((revenue_cur - revenue_pri) / abs(revenue_pri)) if (revenue_cur and revenue_pri and revenue_pri != 0) else None
        flags["extreme_pe"] = trailing_pe > 100 and (rev_growth is None or rev_growth < 0.20)
    else:
        flags["extreme_pe"] = False

    flag_count = sum(1 for v in flags.values() if v)
    data_quality = "full" if available >= 6 else "partial" if available >= 4 else "insufficient"

    if flag_count == 0:  label = "Clean"
    elif flag_count <= 2: label = "Caution"
    elif flag_count <= 4: label = "Warning"
    else:                label = "Avoid"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=float(flag_count),
        max_score=8.0,
        pct=round((8 - flag_count) / 8 * 100, 1),   # inverted: higher % = cleaner
        label=label,
        passed=flag_count <= PASS_THRESHOLD,
        breakdown={
            **{k: ("YES" if v else "no") for k, v in flags.items()},
            "flag_count": flag_count,
            "data_fields_available": available,
        },
        data_quality=data_quality,
    )
    cache_result(r.to_dict())
    return r
