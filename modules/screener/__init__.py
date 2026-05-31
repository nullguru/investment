# -*- coding: utf-8 -*-
"""
Modular screener framework.

Usage:
    from modules.screener import compute_screen, SCREEN_CATALOG, batch_compute_screen

    result = compute_screen("piotroski", "TCS.NS")
    print(result.score, result.label, result.breakdown)
"""

from .base import ScreenResult
from .registry import SCREEN_CATALOG, SCREEN_NAMES, compute_screen, batch_compute_screen

__all__ = [
    "ScreenResult",
    "SCREEN_CATALOG",
    "SCREEN_NAMES",
    "compute_screen",
    "batch_compute_screen",
]
