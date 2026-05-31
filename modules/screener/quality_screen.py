# -*- coding: utf-8 -*-
"""
Quality screen adapter — wraps the existing modules.quality module
so it appears in the screener registry as screen "quality".
"""

from __future__ import annotations

from .base import ScreenResult, safe_float

SCREEN_NAME = "quality"


def compute(symbol: str, force: bool = False, market: str = "india") -> ScreenResult:
    from modules.quality import compute_quality_score

    q = compute_quality_score(symbol, force=force, market=market)

    if q.get("error") or q.get("total_score") is None:
        return ScreenResult(
            screen_name=SCREEN_NAME,
            symbol=symbol,
            score=0.0,
            max_score=100.0,
            pct=0.0,
            label="N/A",
            passed=False,
            breakdown={},
            data_quality="insufficient",
            error=q.get("error") or "No score data",
        )

    total = float(q["total_score"])
    return ScreenResult(
        screen_name=SCREEN_NAME,
        symbol=symbol,
        score=total,
        max_score=100.0,
        pct=total,
        label=q.get("label", ""),
        passed=total >= 65.0,
        breakdown={
            "profitability": q.get("profitability_score"),
            "cash_generation": q.get("cash_generation_score"),
            "financial_strength": q.get("financial_strength_score"),
            "valuation": q.get("valuation_score"),
            "roe_pct": round((q.get("roe") or 0) * 100, 1) if q.get("roe") is not None else None,
            "op_margin_pct": round((q.get("operating_margin") or 0) * 100, 1) if q.get("operating_margin") is not None else None,
            "peg_ratio": q.get("peg_ratio"),
            "data_quality": q.get("data_quality"),
        },
        data_quality=q.get("data_quality", "full"),
    )
