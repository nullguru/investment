# -*- coding: utf-8 -*-
"""
Market data module: fetch company/market data from providers.
Currently supports Yahoo Finance. Extensible for other providers.
"""

from modules.market.yf import get_section_data, clear_cache

__all__ = ["get_section_data", "clear_cache"]
