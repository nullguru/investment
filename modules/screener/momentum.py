# -*- coding: utf-8 -*-
"""
Momentum screen: technical signals for trend and dip-buying.

Components:
  1. 52-week high discount (%)     — how far below 52-week high is current price
  2. 200-day MA position           — price above or below 200-day moving average
  3. RSI (14-day)                  — relative strength index

Score 0-100. Low score = deeply oversold/dipping (potential entry for quality stocks).
High score = strong uptrend.

Usage context:
  - Use alongside Piotroski or quality to identify "quality + dip" opportunities
  - Score < 30 with Piotroski ≥ 6 = potential buy signal
  - Score > 70 = strong momentum (but may be fully valued)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .base import ScreenResult, safe_float, get_ticker, insufficient_result

SCREEN_NAME = "momentum"
PASS_THRESHOLD = 40.0   # below 40 = dip opportunity zone


def _compute_rsi(closes: pd.Series, period: int = 14) -> float | None:
    """Compute RSI from a Series of closing prices."""
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean().iloc[-1]
    avg_loss = loss.rolling(window=period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute(symbol: str, force: bool = False, market: str = "india") -> ScreenResult:
    from .cache import get_cached_result, cache_result

    if not force:
        cached = get_cached_result(SCREEN_NAME, symbol)
        if cached:
            return ScreenResult.from_dict(cached)

    try:
        ticker = get_ticker(symbol, market=market)
        info = ticker.info or {}
        hist = ticker.history(period="1y")
    except Exception as e:
        r = insufficient_result(SCREEN_NAME, symbol, str(e))
        cache_result(r.to_dict())
        return r

    if hist is None or hist.empty or "Close" not in hist.columns:
        r = insufficient_result(SCREEN_NAME, symbol, "No price history available")
        cache_result(r.to_dict())
        return r

    closes = hist["Close"].dropna()
    if len(closes) < 20:
        r = insufficient_result(SCREEN_NAME, symbol, "Insufficient price history (<20 days)")
        cache_result(r.to_dict())
        return r

    price = float(closes.iloc[-1])
    high_52w = float(closes.max())
    low_52w = float(closes.min())

    # 1. Discount from 52-week high (% below peak)
    discount_pct = ((high_52w - price) / high_52w * 100) if high_52w > 0 else 0.0

    # 2. 200-day MA position
    ma_window = min(200, len(closes))
    ma200 = float(closes.rolling(ma_window).mean().iloc[-1])
    vs_ma200_pct = ((price - ma200) / ma200 * 100) if ma200 > 0 else 0.0

    # 50-day MA
    ma50_window = min(50, len(closes))
    ma50 = float(closes.rolling(ma50_window).mean().iloc[-1])
    vs_ma50_pct = ((price - ma50) / ma50 * 100) if ma50 > 0 else 0.0

    # 3. RSI (14-day)
    rsi = _compute_rsi(closes, period=14)

    # Score construction (0-100)
    # Three sub-scores each 0-33.3:
    # MA score: price above both MAs = bullish, below = bearish
    ma_score = 0.0
    if vs_ma200_pct > 5:    ma_score = 33.3   # well above 200-day
    elif vs_ma200_pct > 0:  ma_score = 25.0   # above 200-day
    elif vs_ma200_pct > -5: ma_score = 15.0   # slightly below
    else:                   ma_score = 5.0    # well below

    # Discount score: lower discount = higher price = more bullish trend
    # High discount is actually a buying opportunity signal (low score)
    discount_score = 0.0
    if discount_pct < 5:    discount_score = 33.3   # near 52-week high
    elif discount_pct < 15: discount_score = 25.0
    elif discount_pct < 30: discount_score = 15.0
    elif discount_pct < 50: discount_score = 8.0
    else:                   discount_score = 2.0    # deep discount

    # RSI score: low RSI = oversold = lower momentum score
    rsi_score = 0.0
    if rsi is not None:
        if rsi > 70:    rsi_score = 33.3   # overbought / strong momentum
        elif rsi > 55:  rsi_score = 25.0
        elif rsi > 45:  rsi_score = 18.0
        elif rsi > 30:  rsi_score = 10.0
        else:           rsi_score = 3.0    # oversold

    total_score = round(ma_score + discount_score + rsi_score, 1)

    if total_score >= 70:    label = "Strong Uptrend"
    elif total_score >= 55:  label = "Moderate Uptrend"
    elif total_score >= 40:  label = "Neutral"
    elif total_score >= 25:  label = "Dip Zone"
    else:                    label = "Deeply Oversold"

    # Dip opportunity flag: discount ≥ 20% from 52-wk high
    dip_opportunity = discount_pct >= 20 and (rsi is None or rsi < 45)

    r = ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=total_score,
        max_score=100.0,
        pct=total_score,
        label=label,
        passed=total_score <= PASS_THRESHOLD,   # "passing" for momentum = dip zone
        breakdown={
            "current_price": round(price, 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "discount_from_52w_high_pct": round(discount_pct, 2),
            "vs_200dma_pct": round(vs_ma200_pct, 2),
            "vs_50dma_pct": round(vs_ma50_pct, 2),
            "rsi_14": rsi,
            "dip_opportunity": dip_opportunity,
            "sub_scores": {"ma": ma_score, "discount": discount_score, "rsi": rsi_score},
        },
        data_quality="full",
    )
    cache_result(r.to_dict())
    return r
