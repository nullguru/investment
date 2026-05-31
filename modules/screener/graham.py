# -*- coding: utf-8 -*-
"""
Graham Number: Benjamin Graham's intrinsic value estimate.

Formula: Graham Number = √(22.5 × EPS × BVPS)
  22.5 = 15 (max P/E) × 1.5 (max P/B) — Graham's defensive investor thresholds

Score = margin of safety = (Graham Number - Current Price) / Graham Number × 100
  Positive % = price below Graham Number (potential undervaluation)
  Negative % = price above Graham Number (overvalued by Graham's criteria)

Best suited for stable, profitable, asset-heavy businesses.
High-growth companies may legitimately trade above Graham Number.
"""

from __future__ import annotations

import math

from .base import ScreenResult, safe_float, get_ticker, insufficient_result

SCREEN_NAME = "graham_number"
PASS_THRESHOLD = 0.0    # positive margin of safety = price below Graham Number


def compute(symbol: str, force: bool = False, market: str = "india") -> ScreenResult:
    from .cache import get_cached_result, cache_result

    if not force:
        cached = get_cached_result(SCREEN_NAME, symbol)
        if cached:
            return ScreenResult.from_dict(cached)

    try:
        ticker = get_ticker(symbol, market=market)
        info = ticker.info or {}
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    eps = safe_float(info.get("trailingEps") or info.get("epsTrailingTwelveMonths"))
    bvps = safe_float(info.get("bookValue"))
    price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"))

    if eps is None or bvps is None or price is None:
        r = insufficient_result(SCREEN_NAME, symbol, "Need EPS, BVPS, and current price")
        cache_result(r.to_dict())
        return r

    if eps <= 0 or bvps <= 0:
        r = ScreenResult(
            screen_name=SCREEN_NAME,
            symbol=symbol,
            score=-999.0,
            max_score=100.0,
            pct=0.0,
            label="Not Applicable",
            passed=False,
            breakdown={
                "reason": "Negative EPS or negative book value — Graham Number undefined",
                "eps": eps,
                "bvps": bvps,
                "price": price,
            },
            data_quality="full",
        )
        cache_result(r.to_dict())
        return r

    graham_number = math.sqrt(22.5 * eps * bvps)
    margin_of_safety = (graham_number - price) / graham_number * 100

    pe = price / eps if eps > 0 else None
    pb = price / bvps if bvps > 0 else None

    if margin_of_safety > 30:    label = "Deep Value"
    elif margin_of_safety > 10:  label = "Undervalued"
    elif margin_of_safety > 0:   label = "Slight Discount"
    elif margin_of_safety > -20: label = "Fair Value"
    elif margin_of_safety > -50: label = "Overvalued"
    else:                        label = "Significantly Overvalued"

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=round(margin_of_safety, 2),
        max_score=100.0,
        pct=round(min(max(margin_of_safety + 50, 0), 100), 1),    # center at 50%
        label=label,
        passed=margin_of_safety >= PASS_THRESHOLD,
        breakdown={
            "graham_number": round(graham_number, 2),
            "current_price": price,
            "margin_of_safety_pct": round(margin_of_safety, 2),
            "eps": eps,
            "bvps": bvps,
            "trailing_pe": round(pe, 2) if pe is not None else None,
            "price_to_book": round(pb, 2) if pb is not None else None,
        },
        data_quality="full",
    )
    cache_result(r.to_dict())
    return r
