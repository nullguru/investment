# -*- coding: utf-8 -*-
"""
US stock market tickers: S&P 500 (default) or custom universe CSV.

Tickers have no suffix — US symbols are bare for yfinance (e.g. AAPL, MSFT).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from core.config import INPUT_DIR

# Optional: a local CSV with US tickers (column: Symbol or Ticker)
US_CSV_PATH = INPUT_DIR / "us_universe.csv"

# Fallback: well-known S&P 500 Wikipedia URL
_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def get_sp500_from_wikipedia() -> Optional[Set[str]]:
    """Fetch S&P 500 constituents from Wikipedia. Returns set of bare tickers."""
    try:
        tables = pd.read_html(_SP500_URL)
        df = tables[0]
        # Column is "Symbol" or "Ticker symbol"
        for col in ("Symbol", "Ticker symbol", "Ticker"):
            if col in df.columns:
                symbols = set(df[col].astype(str).str.strip().str.replace(".", "-", regex=False))
                return {s for s in symbols if s and s != "nan"}
    except Exception as e:
        print(f"S&P 500 Wikipedia fetch error: {e}")
    return None


def get_us_symbols_from_file() -> Optional[Set[str]]:
    """Load US tickers from local CSV if present. Columns: Symbol or Ticker."""
    if not US_CSV_PATH.exists():
        return None
    try:
        df = pd.read_csv(US_CSV_PATH, header=0, encoding="utf-8")
        for col in ("Symbol", "Ticker", "TICKER", "ticker", "symbol"):
            if col in df.columns:
                syms = set(df[col].astype(str).str.strip())
                return {s for s in syms if s and s != "nan"}
        return set(df.iloc[:, 0].astype(str).str.strip().dropna())
    except Exception as e:
        print(f"US CSV file error: {e}")
    return None


def get_us_symbols() -> Set[str]:
    """US ticker symbols. Prefer local CSV; fallback to S&P 500 from Wikipedia."""
    symbols = get_us_symbols_from_file()
    if symbols:
        return symbols
    symbols = get_sp500_from_wikipedia()
    return symbols or set()


def get_us_tickers(exchange: str = "all") -> List[str]:
    """
    US equity tickers for yfinance (bare symbols, no suffix).
    exchange: 'all' | 'nasdaq' | 'nyse' (filtering only works with a local CSV that has an Exchange column)
    """
    symbols = get_us_symbols()
    return sorted(symbols)


def get_us_tickers_with_exchange() -> List[Tuple[str, str]]:
    """Returns list of (ticker, 'NASDAQ'|'NYSE'|'US')."""
    # Try to read exchange info from local CSV
    if US_CSV_PATH.exists():
        try:
            df = pd.read_csv(US_CSV_PATH, header=0, encoding="utf-8")
            sym_col = next((c for c in ("Symbol", "Ticker", "TICKER") if c in df.columns), None)
            ex_col = next((c for c in ("Exchange", "exchange", "EXCHANGE") if c in df.columns), None)
            if sym_col:
                result = []
                for _, row in df.iterrows():
                    sym = str(row[sym_col]).strip()
                    if not sym or sym == "nan":
                        continue
                    exchange_val = str(row[ex_col]).strip() if ex_col else "US"
                    result.append((sym, exchange_val))
                return result
        except Exception:
            pass
    # Fallback: all symbols tagged "US"
    return [(s, "US") for s in get_us_tickers()]
