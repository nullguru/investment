# -*- coding: utf-8 -*-
"""
Sharia service: batch computation wrapper.
Calls Yahoo via sharia filter, returns plain dicts for DataFrame/cache.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from modules.sharia.filter import get_sharia_metrics_batch_parallel, is_industry_compliant
from modules.sharia.data import effective_sharia


def compute_sharia_metrics(
    symbols: List[str],
    max_workers: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    market: str = "india",
) -> List[dict]:
    """
    Fetch Sharia metrics for the given symbols (e.g. via Yahoo Finance).
    Returns a list of row dicts suitable for DataFrame/cache.
    market: 'india' (default) or 'us' — affects fiscal year date range.
    """
    total = len(symbols)
    results: List[dict] = []
    batch = get_sharia_metrics_batch_parallel(symbols, max_workers=max_workers, market=market)

    for i, m in enumerate(batch):
        if progress_callback and total:
            progress_callback(i + 1, total)
        industry_ok = getattr(m, "industry_compliant", is_industry_compliant(m.industry, m.sector))
        row = {
            "symbol": m.symbol,
            "name": m.name or m.symbol,
            "total_assets": m.total_assets,
            "cash_and_short_term_investments": m.cash_and_short_term_investments,
            "total_receivables": m.total_receivables,
            "other_revenue": m.other_revenue,
            "total_revenue": m.total_revenue,
            "debt_to_equity_ratio": m.debt_to_equity_ratio,
            "cash_to_assets_pct": m.cash_to_assets_pct,
            "other_revenue_to_revenue_pct": m.other_revenue_to_revenue_pct,
            "receivables_to_assets_pct": m.receivables_to_assets_pct,
            "compliant": m.compliant.value,
            "report_period": m.report_period,
            "period_type": getattr(m, "period_type", "annual"),
            "industry": m.industry,
            "sector": m.sector,
            "market_cap": m.market_cap,
            "industry_compliant": industry_ok,
            "Sharia": effective_sharia(m.compliant.value, industry_ok),
        }
        results.append(row)
    return results
