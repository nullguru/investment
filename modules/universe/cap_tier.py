# -*- coding: utf-8 -*-
"""
Cap tier classification using market cap data from the Sharia cache.

Tier bands (by market cap rank across all cached symbols):
  large  = rank 1-100
  mid    = rank 101-250
  small  = rank 251-500
  micro  = rank 501+

Ranks are assigned by sorting unique symbols by market_cap descending.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

_RANKINGS: dict = {}  # market -> DataFrame, module-level cache


def _strip_suffix(symbol: str) -> str:
    for sfx in (".NS", ".BO", ".ns", ".bo"):
        if symbol.endswith(sfx):
            return symbol[: -len(sfx)]
    return symbol


def load_mcap_rankings(market: str = "india") -> pd.DataFrame:
    """
    Return a DataFrame with columns [symbol, base_symbol, market_cap, rank, cap_tier].
    Derived from the Sharia cache for the given market. Cached in memory after first call.
    """
    global _RANKINGS
    if market in _RANKINGS:
        return _RANKINGS[market]

    from modules.sharia import load_cached_sharia, enrich_cached_sharia

    df = load_cached_sharia(market=market)
    empty = pd.DataFrame(columns=["symbol", "base_symbol", "market_cap", "rank", "cap_tier"])
    if df is None or df.empty:
        _RANKINGS[market] = empty
        return empty

    df = enrich_cached_sharia(df)

    # One row per symbol: take the most recent non-null market_cap
    unique = (
        df[df["market_cap"].notna()]
        .sort_values("report_period", ascending=False)
        .drop_duplicates(subset="symbol", keep="first")[["symbol", "market_cap"]]
        .copy()
    )
    unique["base_symbol"] = unique["symbol"].apply(_strip_suffix)
    unique = unique.sort_values("market_cap", ascending=False).reset_index(drop=True)
    unique["rank"] = unique.index + 1
    unique["cap_tier"] = unique["rank"].apply(get_cap_tier)

    _RANKINGS[market] = unique
    return unique


def get_cap_tier(rank: int) -> str:
    if rank <= 100:
        return "large"
    if rank <= 250:
        return "mid"
    if rank <= 500:
        return "small"
    return "micro"


def get_cap_tier_by_symbol(symbol: str, market: str = "india") -> Optional[str]:
    """Return cap tier for a symbol (with or without .NS/.BO suffix). None if not found."""
    base = _strip_suffix(symbol)
    df = load_mcap_rankings(market=market)
    if df.empty:
        return None
    matches = df[df["base_symbol"] == base]
    if matches.empty:
        return None
    return matches.iloc[0]["cap_tier"]


def get_symbols_for_tier(tier: str, market: str = "india") -> list[str]:
    """Return symbols in the given cap tier, sorted by market cap descending."""
    df = load_mcap_rankings(market=market)
    if df.empty:
        return []
    subset = df[df["cap_tier"] == tier]
    if market == "india":
        # Prefer .NS symbols over .BO
        ns_symbols = subset[subset["symbol"].str.endswith(".NS")]["symbol"].tolist()
        if ns_symbols:
            return ns_symbols
    return subset["symbol"].tolist()


def invalidate_cache(market: Optional[str] = None) -> None:
    """Clear the in-memory rankings cache (e.g. after refreshing Sharia data).
    If market is None, clears all markets.
    """
    global _RANKINGS
    if market is None:
        _RANKINGS.clear()
    else:
        _RANKINGS.pop(market, None)
