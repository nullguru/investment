# -*- coding: utf-8 -*-
"""
Sharia-specific data helpers: cache paths, column definitions, enrichment.
Extracted from the former core/data_layer.py — only Sharia-specific logic lives here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from core.config import CACHE_DIR
from core.cache import load_parquet, save_parquet
from modules.sharia.filter import ShariaStatus, is_industry_compliant

# Sharia cache file (per-market; kept for backward compatibility)
SHARIA_CACHE_PATH = CACHE_DIR / "sharia_metrics_india.parquet"


def get_sharia_cache_path(market: str = "india") -> "Path":
    """Return market-specific Sharia cache path."""
    from pathlib import Path
    return CACHE_DIR / f"sharia_metrics_{market}.parquet"

# Sharia thresholds for highlighting non-compliant cells (must match filter.py)
DEBT_TO_EQUITY_MAX = 0.33
CASH_TO_ASSETS_PCT_MAX = 33.0
OTHER_REVENUE_TO_REVENUE_PCT_MAX = 5.0
RECEIVABLES_TO_ASSETS_PCT_MAX = 50.0

# Default portfolio symbols (base names; resolved to full ticker via universe)
DEFAULT_PORTFOLIO = """TCS
INFY
HCLTECH
HINDUNILVR
GAIL
SUNPHARMA
CIPLA
MARUTI
HAVELLS
CUMMINSIND
ALKEM
POLYCAB
SAFARI
TATATECH"""

# Default US portfolio (common Sharia-compliant US tech/healthcare/consumer stocks)
DEFAULT_PORTFOLIO_US = """AAPL
MSFT
GOOGL
AMZN
NVDA
META
JNJ
COST
LOW
ABBV"""

DEFAULT_PORTFOLIO_MAP: dict = {
    "india": DEFAULT_PORTFOLIO,
    "us": DEFAULT_PORTFOLIO_US,
}

# Shared column order for Sharia tables
SHARIA_TABLE_COLUMNS = [
    "symbol", "name", "exchange", "report_period", "period_type",
    "total_assets", "cash_and_short_term_investments", "total_receivables",
    "other_revenue", "total_revenue", "debt_to_equity_ratio",
    "cash_to_assets_pct", "other_revenue_to_revenue_pct", "receivables_to_assets_pct",
    "industry_compliant", "Sharia", "industry", "sector", "market_cap",
]


# ----- Formatting (pure functions) -----
def _ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def format_date_ordinal(date_str: Any) -> str:
    """Format date string (e.g. 2025-03-31) as '31st March 2025'."""
    if date_str is None or (isinstance(date_str, float) and pd.isna(date_str)):
        return ""
    try:
        dt = pd.Timestamp(date_str)
        day = dt.day
        return f"{day}{_ordinal_suffix(day)} {dt.strftime('%B')} {dt.year}"
    except Exception:
        return str(date_str)


def effective_sharia(compliant_val: Any, industry_ok: Any) -> str:
    """Combined Sharia status: Yes only if ratio-compliant AND industry OK."""
    if pd.isna(industry_ok):
        industry_ok = True
    if compliant_val == ShariaStatus.YES.value and industry_ok:
        return ShariaStatus.YES.value
    if compliant_val == ShariaStatus.NO.value or not industry_ok:
        return ShariaStatus.NO.value
    return ShariaStatus.UNKNOWN.value


# ----- Sharia cache -----
def load_cached_sharia(market: str = "india") -> Optional[pd.DataFrame]:
    """Load Sharia metrics from market-specific cache. Returns None if missing or invalid."""
    path = get_sharia_cache_path(market)
    # Backward-compat: if market-specific file doesn't exist yet, try legacy filename
    if not path.exists() and market == "india":
        legacy = CACHE_DIR / "sharia_metrics.parquet"
        if legacy.exists():
            path = legacy
    df = load_parquet(path)
    if df is not None and "total_assets" in df.columns and "cash_to_assets_pct" in df.columns and "period_type" in df.columns:
        return df
    return None


def save_sharia_cache(df: pd.DataFrame, market: str = "india") -> None:
    """Persist Sharia cache for the given market. Raises on failure."""
    save_parquet(df, get_sharia_cache_path(market))


def enrich_cached_sharia(df: pd.DataFrame) -> pd.DataFrame:
    """Add industry_compliant and Sharia columns if missing."""
    out = df.copy()
    if "industry_compliant" not in out.columns:
        out["industry_compliant"] = out.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    if "Sharia" not in out.columns:
        out["Sharia"] = out.apply(
            lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
        )
    return out


def get_metrics_df_for_counts(
    cached_df: Optional[pd.DataFrame],
    selected_period: str,
) -> Optional[pd.DataFrame]:
    """One row per symbol for the selected period (or latest). Includes effective Sharia."""
    if cached_df is None or cached_df.empty or "compliant" not in cached_df.columns:
        return None
    df = cached_df.dropna(subset=["report_period"]).copy()
    if df.empty:
        return None
    df["_rp_dt"] = pd.to_datetime(df["report_period"], errors="coerce")
    df = df.dropna(subset=["_rp_dt"])
    if selected_period == "All periods":
        df = df.sort_values("_rp_dt").groupby("symbol", as_index=False).last()
    else:
        df = df[df["report_period"].map(format_date_ordinal) == selected_period]
    df = df.drop(columns=["_rp_dt"], errors="ignore")
    df = enrich_cached_sharia(df)
    return df


def get_report_period_options(cached_df: Optional[pd.DataFrame]) -> List[str]:
    """Build report period dropdown options (labels)."""
    if cached_df is None or cached_df.empty or "report_period" not in cached_df.columns:
        return ["All periods"]
    periods = sorted(cached_df["report_period"].dropna().unique().tolist(), reverse=True)
    return ["All periods"] + [format_date_ordinal(p) for p in periods]


# ----- Portfolio helpers -----
def parse_portfolio_symbols(raw: str, all_tickers: List[str], market: str = "india") -> List[str]:
    """Parse comma/newline separated symbols; resolve base names to full ticker."""
    parts = [p.strip().upper() for p in raw.replace(",", "\n").split() if p.strip()]
    all_tickers_set = set(all_tickers)
    seen_bases = set()
    full_tickers = []
    for base in parts:
        if not base:
            continue
        if base in seen_bases:
            continue
        seen_bases.add(base)
        if "." in base:
            full_tickers.append(base)
            continue
        if market == "us":
            # US: bare tickers are already valid — just match directly
            if base in all_tickers_set:
                full_tickers.append(base)
            else:
                full_tickers.append(base)  # allow unknown US tickers through
        else:
            # India: resolve base name to .NS or .BO
            for suffix in (".NS", ".BO"):
                candidate = base + suffix
                if candidate in all_tickers_set:
                    full_tickers.append(candidate)
                    break
            else:
                full_tickers.append(base)
    return full_tickers


def resolve_search_to_ticker(query: str, all_tickers: List[str], market: str = "india") -> Optional[str]:
    """Resolve search query to a ticker.
    India: TCS → TCS.NS  |  US: AAPL → AAPL (bare, no suffix)
    Returns None if no match found.
    """
    q = (query or "").strip().upper()
    if not q:
        return None
    # Exact match works for both markets
    if q in all_tickers:
        return q
    if market == "india":
        # Try Indian exchange suffixes
        for suffix in (".NS", ".BO"):
            candidate = q + suffix
            if candidate in all_tickers:
                return candidate
    # No match
    return None
