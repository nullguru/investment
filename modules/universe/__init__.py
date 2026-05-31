# -*- coding: utf-8 -*-
"""
Universe module: ticker management across markets.
Currently supports Indian market (BSE/NSE). Extensible for US, etc.
"""

from modules.universe.indian import (
    get_indian_tickers,
    get_indian_tickers_with_exchange,
    get_nse_symbols,
    get_bse_symbols,
)
from modules.universe.us import (
    get_us_tickers,
    get_us_tickers_with_exchange,
)
from modules.universe.cap_tier import (
    load_mcap_rankings,
    get_cap_tier,
    get_cap_tier_by_symbol,
    get_symbols_for_tier,
    invalidate_cache as invalidate_cap_cache,
)
from modules.universe.suggest import suggest_candidates
from typing import Dict, List, Tuple

SUPPORTED_MARKETS = ("india", "us")


def load_universe(market: str = "india") -> Tuple[List[str], Dict[str, str]]:
    """
    Load ticker list and symbol -> exchange map for a market.
    Returns (tickers, exchange_map).

    Supported markets: 'india' (NSE/BSE), 'us' (S&P 500 / custom CSV)
    """
    if market == "india":
        tickers = get_indian_tickers()
        with_exchange = get_indian_tickers_with_exchange()
        exchange_map = {t: ex for t, ex in with_exchange}
        return tickers, exchange_map
    if market == "us":
        tickers = get_us_tickers()
        with_exchange = get_us_tickers_with_exchange()
        exchange_map = {t: ex for t, ex in with_exchange}
        return tickers, exchange_map
    raise ValueError(f"Unknown market: {market!r}. Supported: {', '.join(SUPPORTED_MARKETS)}")


__all__ = [
    "load_universe",
    "SUPPORTED_MARKETS",
    "get_indian_tickers",
    "get_indian_tickers_with_exchange",
    "get_nse_symbols",
    "get_bse_symbols",
    "get_us_tickers",
    "get_us_tickers_with_exchange",
    "load_mcap_rankings",
    "get_cap_tier",
    "get_cap_tier_by_symbol",
    "get_symbols_for_tier",
    "invalidate_cap_cache",
    "suggest_candidates",
]
