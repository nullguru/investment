# -*- coding: utf-8 -*-
"""
Piotroski F-Score (0-9): 9 binary financial health criteria.

Profitability (4): ROA>0, OCF>0, improving ROA, accruals quality (OCF > net income)
Leverage/Liquidity (3): declining long-term debt ratio, improving current ratio, no dilution
Efficiency (2): improving gross margin, improving asset turnover

Score ≥ 7 = strong (buy signal), 5-6 = decent, ≤ 2 = avoid
"""

from __future__ import annotations

from .base import ScreenResult, safe_float, df_get, get_ticker, insufficient_result

SCREEN_NAME = "piotroski"
PASS_THRESHOLD = 5


def compute(symbol: str, force: bool = False, market: str = "india") -> ScreenResult:
    from .cache import get_cached_result, cache_result

    if not force:
        cached = get_cached_result(SCREEN_NAME, symbol)
        if cached:
            return ScreenResult.from_dict(cached)

    try:
        ticker = get_ticker(symbol, market=market)
        info = ticker.info or {}
        inc = ticker.financials        # index=metrics, columns=dates (most recent first)
        bal = ticker.balance_sheet
        cf = ticker.cashflow
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    if inc is None or inc.empty or len(inc.columns) < 2:
        r = insufficient_result(SCREEN_NAME, symbol, "Need ≥2 years of income data")
        cache_result(r.to_dict())
        return r

    # col=0: current year, col=1: prior year
    revenue_cur = df_get(inc, ["Total Revenue", "Revenue"], 0)
    revenue_pri = df_get(inc, ["Total Revenue", "Revenue"], 1)
    ni_cur = df_get(inc, ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"], 0)
    ni_pri = df_get(inc, ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"], 1)
    cogs_cur = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 0)
    cogs_pri = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 1)

    ta_cur = df_get(bal, ["Total Assets"], 0) if bal is not None and not bal.empty else None
    ta_pri = df_get(bal, ["Total Assets"], 1) if bal is not None and len(bal.columns) > 1 else None
    ca_cur = df_get(bal, ["Current Assets", "Total Current Assets"], 0) if bal is not None else None
    ca_pri = df_get(bal, ["Current Assets", "Total Current Assets"], 1) if bal is not None and len((bal.columns if bal is not None else [])  ) > 1 else None
    cl_cur = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 0) if bal is not None else None
    cl_pri = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 1) if bal is not None and bal is not None and len(bal.columns) > 1 else None
    ltd_cur = df_get(bal, ["Long Term Debt", "Long-Term Debt", "LongTermDebt"], 0) if bal is not None else None
    ltd_pri = df_get(bal, ["Long Term Debt", "Long-Term Debt", "LongTermDebt"], 1) if bal is not None and len(bal.columns) > 1 else None
    shares_cur = df_get(bal, ["Ordinary Shares Number", "Share Issued", "Common Stock"], 0) if bal is not None else None
    shares_pri = df_get(bal, ["Ordinary Shares Number", "Share Issued", "Common Stock"], 1) if bal is not None and len(bal.columns) > 1 else None

    if shares_cur is None:
        shares_cur = safe_float(info.get("sharesOutstanding"))

    ocf_cur = df_get(cf, ["Operating Cash Flow", "Cash From Operating Activities"], 0) if cf is not None else None

    breakdown: dict = {}
    score = 0

    # F1: ROA > 0
    roa_cur = (ni_cur / ta_cur) if (ni_cur is not None and ta_cur and ta_cur != 0) else None
    f1 = 1 if (roa_cur is not None and roa_cur > 0) else 0
    score += f1
    breakdown["f1_roa_positive"] = {"score": f1, "roa": round(roa_cur * 100, 2) if roa_cur is not None else None}

    # F2: OCF > 0
    f2 = 1 if (ocf_cur is not None and ocf_cur > 0) else 0
    score += f2
    breakdown["f2_ocf_positive"] = {"score": f2, "ocf": ocf_cur}

    # F3: ROA improving
    roa_pri = (ni_pri / ta_pri) if (ni_pri is not None and ta_pri and ta_pri != 0) else None
    f3 = 1 if (roa_cur is not None and roa_pri is not None and roa_cur > roa_pri) else 0
    score += f3
    breakdown["f3_roa_improving"] = {
        "score": f3,
        "roa_cur_pct": round(roa_cur * 100, 2) if roa_cur is not None else None,
        "roa_pri_pct": round(roa_pri * 100, 2) if roa_pri is not None else None,
    }

    # F4: Accruals quality (OCF/TA > NI/TA means earnings backed by cash)
    ocf_ta = (ocf_cur / ta_cur) if (ocf_cur is not None and ta_cur and ta_cur != 0) else None
    f4 = 1 if (ocf_ta is not None and roa_cur is not None and ocf_ta > roa_cur) else 0
    score += f4
    breakdown["f4_accruals_quality"] = {
        "score": f4,
        "ocf_ta_pct": round(ocf_ta * 100, 2) if ocf_ta is not None else None,
        "ni_ta_pct": round(roa_cur * 100, 2) if roa_cur is not None else None,
    }

    # F5: Long-term leverage declining
    lev_cur = (ltd_cur / ta_cur) if (ltd_cur is not None and ta_cur and ta_cur != 0) else None
    lev_pri = (ltd_pri / ta_pri) if (ltd_pri is not None and ta_pri and ta_pri != 0) else None
    f5 = 1 if (lev_cur is not None and lev_pri is not None and lev_cur < lev_pri) else 0
    score += f5
    breakdown["f5_leverage_declining"] = {
        "score": f5,
        "lev_cur_pct": round(lev_cur * 100, 2) if lev_cur is not None else None,
        "lev_pri_pct": round(lev_pri * 100, 2) if lev_pri is not None else None,
    }

    # F6: Current ratio improving
    cr_cur = (ca_cur / cl_cur) if (ca_cur is not None and cl_cur and cl_cur != 0) else None
    cr_pri = (ca_pri / cl_pri) if (ca_pri is not None and cl_pri and cl_pri != 0) else None
    f6 = 1 if (cr_cur is not None and cr_pri is not None and cr_cur > cr_pri) else 0
    score += f6
    breakdown["f6_liquidity_improving"] = {
        "score": f6,
        "cr_cur": round(cr_cur, 2) if cr_cur is not None else None,
        "cr_pri": round(cr_pri, 2) if cr_pri is not None else None,
    }

    # F7: No dilution (shares not materially increased)
    f7 = 0
    if shares_cur is not None and shares_pri is not None:
        f7 = 1 if shares_cur <= shares_pri * 1.02 else 0
    breakdown["f7_no_dilution"] = {
        "score": f7,
        "shares_cur": shares_cur,
        "shares_pri": shares_pri,
    }
    score += f7

    # F8: Gross margin improving
    gm_cur = ((revenue_cur - cogs_cur) / revenue_cur) if (revenue_cur and cogs_cur is not None and revenue_cur != 0) else None
    gm_pri = ((revenue_pri - cogs_pri) / revenue_pri) if (revenue_pri and cogs_pri is not None and revenue_pri != 0) else None
    f8 = 1 if (gm_cur is not None and gm_pri is not None and gm_cur > gm_pri) else 0
    score += f8
    breakdown["f8_gross_margin_improving"] = {
        "score": f8,
        "gm_cur_pct": round(gm_cur * 100, 2) if gm_cur is not None else None,
        "gm_pri_pct": round(gm_pri * 100, 2) if gm_pri is not None else None,
    }

    # F9: Asset turnover improving
    at_cur = (revenue_cur / ta_cur) if (revenue_cur and ta_cur and ta_cur != 0) else None
    at_pri = (revenue_pri / ta_pri) if (revenue_pri and ta_pri and ta_pri != 0) else None
    f9 = 1 if (at_cur is not None and at_pri is not None and at_cur > at_pri) else 0
    score += f9
    breakdown["f9_asset_turnover_improving"] = {
        "score": f9,
        "at_cur": round(at_cur, 3) if at_cur is not None else None,
        "at_pri": round(at_pri, 3) if at_pri is not None else None,
    }

    available = sum(1 for v in [roa_cur, ocf_cur, lev_cur, cr_cur, gm_cur, at_cur] if v is not None)
    data_quality = "full" if available >= 5 else "partial" if available >= 3 else "insufficient"

    if score >= 8:   label = "Strong"
    elif score >= 7: label = "Good"
    elif score >= 5: label = "Average"
    elif score >= 3: label = "Weak"
    else:            label = "Poor"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=float(score),
        max_score=9.0,
        pct=round(score / 9.0 * 100, 1),
        label=label,
        passed=score >= PASS_THRESHOLD,
        breakdown=breakdown,
        data_quality=data_quality,
    )
    cache_result(r.to_dict())
    return r
