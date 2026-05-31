# -*- coding: utf-8 -*-
"""
Indian stock market tickers: BSE and NSE.
Combined universe with .NS (NSE) and .BO (BSE) suffixes for yfinance.
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Optional: nsetools for NSE symbols
try:
    from nsetools import Nse
    HAS_NSETOOLS = True
except ImportError:
    HAS_NSETOOLS = False

import pandas as pd

from core.config import INPUT_DIR

BSE_CSV_PATH = INPUT_DIR / "Equity.csv"
NSE_EXCEL_PATH = INPUT_DIR / "Average_MCAP_NSE.xlsx"


def get_nse_symbols_from_nsetools() -> Optional[Set[str]]:
    """Fetch NSE symbols using nsetools. Returns set of base symbols (no suffix)."""
    if not HAS_NSETOOLS:
        return None
    try:
        nse = Nse()
        codes = nse.get_stock_codes()
        if isinstance(codes, dict):
            return set(k for k in codes if k != "SYMBOL" and isinstance(k, str))
        return set(codes) if codes else None
    except Exception as e:
        print(f"NSE (nsetools) error: {e}")
        return None


def get_nse_symbols_from_file() -> Optional[Set[str]]:
    """Load NSE symbols from local Excel if present. Column expected: Symbol."""
    if not NSE_EXCEL_PATH.exists():
        return None
    try:
        df = pd.read_excel(NSE_EXCEL_PATH)
        if "Symbol" in df.columns:
            return set(df["Symbol"].astype(str).dropna())
        return set(df.iloc[:, 0].astype(str).dropna())
    except Exception as e:
        print(f"NSE file error: {e}")
        return None


def get_nse_symbols() -> Set[str]:
    """NSE symbols (base names, no suffix). Prefer nsetools; fallback to file."""
    symbols = get_nse_symbols_from_nsetools()
    if symbols:
        return symbols
    symbols = get_nse_symbols_from_file()
    return symbols or set()


def get_bse_symbols_from_file() -> Optional[Set[str]]:
    """Load BSE symbols from local CSV. Columns: Security Id or SC_CODE."""
    if not BSE_CSV_PATH.exists():
        return None
    try:
        df = pd.read_csv(BSE_CSV_PATH, header=0, encoding="utf-8")
        for col in ("Security Id", "SECURITY_ID", "Security ID", "SC_CODE"):
            if col in df.columns:
                return set(df[col].astype(str).dropna())
        return set(df.iloc[:, 0].astype(str).dropna())
    except Exception as e:
        print(f"BSE file error: {e}")
        return None


def get_bse_symbols() -> Set[str]:
    """BSE symbols (base names). From local CSV only (download from BSE List_Scrips)."""
    return get_bse_symbols_from_file() or set()


def get_indian_tickers(
    use_nse: bool = True,
    use_bse: bool = True,
    nse_only_suffix: str = ".NS",
    bse_only_suffix: str = ".BO",
) -> List[str]:
    """
    Combined Indian equity tickers for yfinance.
    - Listed on both: use NSE (.NS).
    - NSE only: .NS
    - BSE only: .BO
    """
    nse_set = get_nse_symbols() if use_nse else set()
    bse_set = get_bse_symbols() if use_bse else set()

    common = nse_set & bse_set
    only_nse = nse_set - bse_set
    only_bse = bse_set - nse_set

    out: List[str] = []
    for s in sorted(common):
        out.append(str(s) + nse_only_suffix)
    for s in sorted(only_nse):
        out.append(str(s) + nse_only_suffix)
    for s in sorted(only_bse):
        out.append(str(s) + bse_only_suffix)

    return out


def get_indian_tickers_with_exchange() -> List[Tuple[str, str]]:
    """Returns list of (ticker_with_suffix, 'NSE'|'BSE')."""
    nse_set = get_nse_symbols()
    bse_set = get_bse_symbols()
    common = nse_set & bse_set
    only_nse = nse_set - bse_set
    only_bse = bse_set - nse_set

    out: List[Tuple[str, str]] = []
    for s in sorted(common):
        out.append((str(s) + ".NS", "NSE"))
    for s in sorted(only_nse):
        out.append((str(s) + ".NS", "NSE"))
    for s in sorted(only_bse):
        out.append((str(s) + ".BO", "BSE"))
    return out
