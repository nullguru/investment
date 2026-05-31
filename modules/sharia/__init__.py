# -*- coding: utf-8 -*-
"""
Sharia module: Islamic finance compliance screening.
Computes debt, cash, receivables, and revenue ratios against Sharia thresholds.
"""

from modules.sharia.filter import (
    ShariaStatus,
    ShariaMetrics,
    get_sharia_metrics,
    get_sharia_metrics_batch,
    get_sharia_metrics_batch_parallel,
    sharia_metrics_to_dataframe,
    is_industry_compliant,
    DEBT_TO_EQUITY_MAX,
    CASH_TO_ASSETS_MAX,
    OTHER_REVENUE_TO_REVENUE_MAX,
    RECEIVABLES_TO_ASSETS_MAX,
)
from modules.sharia.service import compute_sharia_metrics
from modules.sharia.data import (
    SHARIA_CACHE_PATH,
    SHARIA_TABLE_COLUMNS,
    DEFAULT_PORTFOLIO,
    DEFAULT_PORTFOLIO_US,
    DEFAULT_PORTFOLIO_MAP,
    get_sharia_cache_path,
    load_cached_sharia,
    save_sharia_cache,
    enrich_cached_sharia,
    effective_sharia,
    format_date_ordinal,
    get_metrics_df_for_counts,
    get_report_period_options,
    parse_portfolio_symbols,
    resolve_search_to_ticker,
)

__all__ = [
    "ShariaStatus",
    "ShariaMetrics",
    "get_sharia_metrics",
    "get_sharia_metrics_batch",
    "get_sharia_metrics_batch_parallel",
    "sharia_metrics_to_dataframe",
    "is_industry_compliant",
    "compute_sharia_metrics",
    "SHARIA_CACHE_PATH",
    "SHARIA_TABLE_COLUMNS",
    "DEFAULT_PORTFOLIO",
    "DEFAULT_PORTFOLIO_US",
    "DEFAULT_PORTFOLIO_MAP",
    "get_sharia_cache_path",
    "load_cached_sharia",
    "save_sharia_cache",
    "enrich_cached_sharia",
    "effective_sharia",
    "format_date_ordinal",
    "get_metrics_df_for_counts",
    "get_report_period_options",
    "parse_portfolio_symbols",
    "resolve_search_to_ticker",
]
