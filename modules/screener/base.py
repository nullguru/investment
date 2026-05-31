# -*- coding: utf-8 -*-
"""
Base types shared across all screener modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd


@dataclass
class ScreenResult:
    screen_name: str
    symbol: str
    score: float
    max_score: float
    pct: float
    label: str
    passed: bool
    breakdown: dict = field(default_factory=dict)
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data_quality: str = "full"   # "full" / "partial" / "insufficient"
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "screen_name": self.screen_name,
            "symbol": self.symbol,
            "score": self.score,
            "max_score": self.max_score,
            "pct": round(self.pct, 1),
            "label": self.label,
            "passed": self.passed,
            "breakdown": self.breakdown,
            "computed_at": self.computed_at,
            "data_quality": self.data_quality,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScreenResult":
        return cls(
            screen_name=d.get("screen_name", ""),
            symbol=d.get("symbol", ""),
            score=d.get("score", 0.0),
            max_score=d.get("max_score", 1.0),
            pct=d.get("pct", 0.0),
            label=d.get("label", ""),
            passed=d.get("passed", False),
            breakdown=d.get("breakdown", {}),
            computed_at=d.get("computed_at", ""),
            data_quality=d.get("data_quality", "insufficient"),
            error=d.get("error"),
        )


def safe_float(v: Any) -> Optional[float]:
    """Return float or None; discard NaN/Inf."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def df_get(df: Optional[pd.DataFrame], row_names, col: int = 0) -> Optional[float]:
    """Extract float from yfinance DataFrame by row name(s) and column index (0 = most recent)."""
    if df is None or df.empty:
        return None
    names = [row_names] if isinstance(row_names, str) else row_names
    for name in names:
        if name in df.index:
            try:
                if col < len(df.columns):
                    v = df.loc[name, df.columns[col]]
                    return safe_float(v)
            except (KeyError, TypeError):
                continue
    return None


def get_ticker(symbol: str, market: str = "india"):
    """
    Get yfinance Ticker for symbol.
    market: 'india' (default, adds .NS suffix to bare symbols) or 'us' (no suffix).
    """
    import yfinance as yf
    from modules.market.yf import _ensure_ticker
    return yf.Ticker(_ensure_ticker(symbol, market))


def insufficient_result(screen_name: str, symbol: str, reason: str) -> ScreenResult:
    return ScreenResult(
        screen_name=screen_name,
        symbol=symbol,
        score=0.0,
        max_score=1.0,
        pct=0.0,
        label="N/A",
        passed=False,
        breakdown={},
        data_quality="insufficient",
        error=reason,
    )
