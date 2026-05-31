# -*- coding: utf-8 -*-
"""
Portfolio module: custom portfolio analysis.
Currently supports Sharia portfolio tracking. Extensible for P&L, allocation, etc.
"""

from modules.portfolio.sharia_index import (
    analyze_personal_index,
    list_benchmarks,
    load_benchmark,
    parse_holdings_arg,
    parse_holdings_text,
)
from modules.portfolio.policy import analyze_portfolio
from modules.portfolio.sizer import compute_position_size

__all__ = [
    "analyze_personal_index",
    "list_benchmarks",
    "load_benchmark",
    "parse_holdings_arg",
    "parse_holdings_text",
    "analyze_portfolio",
    "compute_position_size",
]
