# -*- coding: utf-8 -*-
"""
Beneish M-Score: 8-variable earnings manipulation detector.

M = -4.84 + 0.920×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
       + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

Variables:
  DSRI  = Days Sales in Receivables Index   (receivables spiking relative to sales → revenue fraud)
  GMI   = Gross Margin Index                 (deteriorating margin → manipulation incentive)
  AQI   = Asset Quality Index                (rising non-current / low-quality assets)
  SGI   = Sales Growth Index                 (high growth = higher manipulation pressure)
  DEPI  = Depreciation Index                 (slowing depreciation = asset life extension)
  SGAI  = SG&A Index                         (rising overhead relative to sales)
  TATA  = Total Accruals to Total Assets     (HIGHEST weight: gap between earnings and cash)
  LVGI  = Leverage Index                     (rising debt = pressure to hit earnings)

M < -2.22 = unlikely manipulator (clean)
-2.22 to -1.78 = gray zone
M > -1.78 = likely manipulator (investigate)
"""

from __future__ import annotations

from .base import ScreenResult, safe_float, df_get, get_ticker, insufficient_result

SCREEN_NAME = "beneish_m"
PASS_THRESHOLD = -1.78   # below this = pass (not a manipulator)


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
        cf = ticker.cashflow
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    if inc is None or inc.empty or len(inc.columns) < 2:
        r = insufficient_result(SCREEN_NAME, symbol, "Need ≥2 years of income data")
        cache_result(r.to_dict())
        return r

    has_bal2 = bal is not None and not bal.empty and len(bal.columns) >= 2
    has_cf = cf is not None and not cf.empty

    # Income statement: current (col 0) and prior (col 1)
    rev_t  = df_get(inc, ["Total Revenue", "Revenue"], 0)
    rev_t1 = df_get(inc, ["Total Revenue", "Revenue"], 1)
    cogs_t  = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 0)
    cogs_t1 = df_get(inc, ["Cost Of Revenue", "Cost of Revenue", "Cost Of Goods Sold"], 1)
    sga_t  = df_get(inc, ["Selling General Administrative", "Selling General And Administration", "Operating Expense"], 0)
    sga_t1 = df_get(inc, ["Selling General Administrative", "Selling General And Administration", "Operating Expense"], 1)

    # Balance sheet
    ta_t  = df_get(bal, ["Total Assets"], 0) if bal is not None and not bal.empty else None
    ta_t1 = df_get(bal, ["Total Assets"], 1) if has_bal2 else None
    ar_t  = df_get(bal, ["Accounts Receivable", "Net Receivables", "Receivables"], 0) if bal is not None else None
    ar_t1 = df_get(bal, ["Accounts Receivable", "Net Receivables", "Receivables"], 1) if has_bal2 else None
    ca_t  = df_get(bal, ["Current Assets", "Total Current Assets"], 0) if bal is not None else None
    ca_t1 = df_get(bal, ["Current Assets", "Total Current Assets"], 1) if has_bal2 else None
    ppe_t  = df_get(bal, ["Net PPE", "Property Plant And Equipment Net", "Net Property Plant And Equipment"], 0) if bal is not None else None
    ppe_t1 = df_get(bal, ["Net PPE", "Property Plant And Equipment Net", "Net Property Plant And Equipment"], 1) if has_bal2 else None
    ltd_t  = df_get(bal, ["Long Term Debt", "Long-Term Debt", "LongTermDebt"], 0) if bal is not None else None
    ltd_t1 = df_get(bal, ["Long Term Debt", "Long-Term Debt", "LongTermDebt"], 1) if has_bal2 else None
    cl_t  = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 0) if bal is not None else None

    # Cash flow
    dep_t  = df_get(cf, ["Depreciation And Amortization", "Depreciation", "Depreciation Depletion And Amortization"], 0) if has_cf else None
    dep_t1 = df_get(cf, ["Depreciation And Amortization", "Depreciation", "Depreciation Depletion And Amortization"], 1) if has_cf and cf is not None and len(cf.columns) >= 2 else None
    ocf_t  = df_get(cf, ["Operating Cash Flow", "Cash From Operating Activities"], 0) if has_cf else None
    ni_t   = df_get(inc, ["Net Income", "Net Income Common Stockholders"], 0)

    breakdown: dict = {}
    computed_vars = 0

    # DSRI: Days Sales in Receivables Index
    dsri = None
    if ar_t is not None and rev_t and ar_t1 is not None and rev_t1 and rev_t != 0 and rev_t1 != 0:
        dsri = (ar_t / rev_t) / (ar_t1 / rev_t1)
        computed_vars += 1
    breakdown["dsri"] = round(dsri, 4) if dsri is not None else None

    # GMI: Gross Margin Index
    gmi = None
    if rev_t and cogs_t is not None and rev_t1 and cogs_t1 is not None and rev_t != 0 and rev_t1 != 0:
        gm_t  = (rev_t  - cogs_t)  / rev_t
        gm_t1 = (rev_t1 - cogs_t1) / rev_t1
        if gm_t != 0:
            gmi = gm_t1 / gm_t
        computed_vars += 1
    breakdown["gmi"] = round(gmi, 4) if gmi is not None else None

    # AQI: Asset Quality Index
    aqi = None
    if ta_t and ca_t is not None and ppe_t is not None and ta_t1 and ca_t1 is not None and ppe_t1 is not None and ta_t != 0 and ta_t1 != 0:
        nca_ratio_t  = 1 - (ca_t  + ppe_t)  / ta_t
        nca_ratio_t1 = 1 - (ca_t1 + ppe_t1) / ta_t1
        if nca_ratio_t1 != 0:
            aqi = nca_ratio_t / nca_ratio_t1
        computed_vars += 1
    breakdown["aqi"] = round(aqi, 4) if aqi is not None else None

    # SGI: Sales Growth Index
    sgi = None
    if rev_t and rev_t1 and rev_t1 != 0:
        sgi = rev_t / rev_t1
        computed_vars += 1
    breakdown["sgi"] = round(sgi, 4) if sgi is not None else None

    # DEPI: Depreciation Index
    depi = None
    if dep_t is not None and ppe_t is not None and dep_t1 is not None and ppe_t1 is not None:
        denom_t  = ppe_t  + dep_t  if dep_t  > 0 else None
        denom_t1 = ppe_t1 + dep_t1 if dep_t1 > 0 else None
        if denom_t and denom_t1 and denom_t != 0:
            depi = (dep_t1 / denom_t1) / (dep_t / denom_t)
            computed_vars += 1
    breakdown["depi"] = round(depi, 4) if depi is not None else None

    # SGAI: SG&A Index
    sgai = None
    if sga_t is not None and rev_t and sga_t1 is not None and rev_t1 and rev_t != 0 and rev_t1 != 0:
        sgai = (sga_t / rev_t) / (sga_t1 / rev_t1)
        computed_vars += 1
    breakdown["sgai"] = round(sgai, 4) if sgai is not None else None

    # TATA: Total Accruals to Total Assets (highest weight = 4.679)
    # Accruals = Net Income - Operating Cash Flow
    tata = None
    if ni_t is not None and ocf_t is not None and ta_t and ta_t != 0:
        tata = (ni_t - ocf_t) / ta_t
        computed_vars += 1
    breakdown["tata"] = round(tata, 4) if tata is not None else None

    # LVGI: Leverage Index
    lvgi = None
    if ltd_t is not None and cl_t is not None and ta_t and ta_t1 and ta_t != 0 and ta_t1 != 0:
        # Simplified: long-term debt / total assets
        ltd_t1_val = ltd_t1 if ltd_t1 is not None else 0.0
        ratio_t  = (ltd_t + cl_t) / ta_t
        # For prior year use what we have
        cl_t1 = df_get(bal, ["Current Liabilities", "Total Current Liabilities", "Current Liabilities Net Minority Interest"], 1) if has_bal2 else cl_t
        cl_t1 = cl_t1 if cl_t1 is not None else cl_t
        ratio_t1 = (ltd_t1_val + cl_t1) / ta_t1
        if ratio_t1 != 0:
            lvgi = ratio_t / ratio_t1
            computed_vars += 1
    breakdown["lvgi"] = round(lvgi, 4) if lvgi is not None else None

    if computed_vars < 4:
        r = insufficient_result(SCREEN_NAME, symbol, f"Only {computed_vars}/8 M-Score variables available")
        cache_result(r.to_dict())
        return r

    m_score = (
        -4.84
        + 0.920 * (dsri  or 1.0)
        + 0.528 * (gmi   or 1.0)
        + 0.404 * (aqi   or 1.0)
        + 0.892 * (sgi   or 1.0)
        + 0.115 * (depi  or 1.0)
        - 0.172 * (sgai  or 1.0)
        + 4.679 * (tata  or 0.0)
        - 0.327 * (lvgi  or 1.0)
    )

    if m_score < -2.22:  label = "Clean"
    elif m_score < -1.78: label = "Gray Zone"
    else:                 label = "Manipulation Risk"

    data_quality = "full" if computed_vars >= 7 else "partial"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=round(m_score, 3),
        max_score=-1.78,          # "passing" score is anything below -1.78
        pct=round(min(max((-m_score - 1.78) / 1.5 * 100, 0), 100), 1),
        label=label,
        passed=m_score < PASS_THRESHOLD,
        breakdown={**breakdown, "m_score": round(m_score, 3), "vars_computed": computed_vars},
        data_quality=data_quality,
    )
    cache_result(r.to_dict())
    return r
