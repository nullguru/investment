# -*- coding: utf-8 -*-
"""
Screen registry — all available screens with metadata.

Adding a new screen: implement compute(symbol, force) -> ScreenResult in a new
module, then add an entry to SCREEN_CATALOG and register in compute_screen().
"""

from __future__ import annotations

from typing import NamedTuple


class ScreenMeta(NamedTuple):
    name: str
    description: str
    score_range: str
    pass_threshold: float
    screen_type: str  # quality | value | safety | integrity | trend | risk
    pass_label: str   # human-readable interpretation of "pass"


SCREEN_CATALOG: dict[str, ScreenMeta] = {
    "quality": ScreenMeta(
        name="quality",
        description="4-dimension quality score: profitability, cash generation, financial strength, valuation (0-100)",
        score_range="0-100",
        pass_threshold=65.0,
        screen_type="quality",
        pass_label="≥65 = Good, ≥80 = Exceptional",
    ),
    "piotroski": ScreenMeta(
        name="piotroski",
        description="Piotroski F-Score: 9 binary financial health criteria covering profitability, leverage, and efficiency",
        score_range="0-9",
        pass_threshold=5.0,
        screen_type="quality",
        pass_label="≥7 = Strong buy signal, ≥5 = Decent, ≤2 = Avoid",
    ),
    "altman_z": ScreenMeta(
        name="altman_z",
        description="Altman Z-Score: 5-variable bankruptcy risk model. Z>3 = safe, 1.8-3 = gray zone, <1.8 = distress",
        score_range="0-∞ (typically 0-8)",
        pass_threshold=1.8,
        screen_type="safety",
        pass_label=">3.0 = Safe, 1.8-3.0 = Gray zone, <1.8 = High risk",
    ),
    "beneish_m": ScreenMeta(
        name="beneish_m",
        description="Beneish M-Score: 8-variable earnings manipulation detector. M<-2.22 = clean, M>-1.78 = likely manipulator",
        score_range="typically -3 to 0",
        pass_threshold=-1.78,
        screen_type="integrity",
        pass_label="<-2.22 = Clean, -2.22 to -1.78 = Gray zone, >-1.78 = Manipulation risk",
    ),
    "magic_formula": ScreenMeta(
        name="magic_formula",
        description="Greenblatt Magic Formula: ROCE + Earnings Yield. Identifies quality businesses at cheap prices",
        score_range="0-100 (composite percentile)",
        pass_threshold=60.0,
        screen_type="value",
        pass_label="ROCE>15% and Earnings Yield>7% = attractive",
    ),
    "graham_number": ScreenMeta(
        name="graham_number",
        description="Graham Number: √(22.5 × EPS × BVPS). Margin of safety = (Graham Number - Price) / Graham Number",
        score_range="-∞ to +∞ (% margin of safety)",
        pass_threshold=0.0,
        screen_type="value",
        pass_label=">0% = price below Graham Number (undervalued)",
    ),
    "momentum": ScreenMeta(
        name="momentum",
        description="Momentum signals: 52-week high discount, 200-day MA position, RSI. Useful for dip-buying quality stocks",
        score_range="0-100",
        pass_threshold=40.0,
        screen_type="trend",
        pass_label="<40 = deeply oversold (potential entry), >70 = strong uptrend",
    ),
    "red_flags": ScreenMeta(
        name="red_flags",
        description="Composite red flag detector: counts hard-avoid signals (poor cash conversion, high debt, FCF negative, etc.)",
        score_range="0-8 flags (lower = safer)",
        pass_threshold=2.0,
        screen_type="risk",
        pass_label="0 = clean, 1-2 = caution, 3+ = avoid",
    ),
}

SCREEN_NAMES = list(SCREEN_CATALOG.keys())


def compute_screen(name: str, symbol: str, force: bool = False, market: str = "india"):
    """Dispatch to the correct screen module and return ScreenResult."""
    if name == "quality":
        from .quality_screen import compute
    elif name == "piotroski":
        from .piotroski import compute
    elif name == "altman_z":
        from .altman import compute
    elif name == "beneish_m":
        from .beneish import compute
    elif name == "magic_formula":
        from .magic_formula import compute
    elif name == "graham_number":
        from .graham import compute
    elif name == "momentum":
        from .momentum import compute
    elif name == "red_flags":
        from .red_flags import compute
    else:
        from .base import insufficient_result
        return insufficient_result(name, symbol, f"Unknown screen: {name}")
    return compute(symbol, force=force, market=market)


def batch_compute_screen(
    screen_name: str,
    symbols: list[str],
    workers: int = 5,
    force: bool = False,
    progress_cb=None,
    market: str = "india",
) -> list[dict]:
    """Parallel batch computation for a single screen across symbols."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: dict[str, dict] = {}
    total = len(symbols)

    def _one(sym: str) -> tuple[str, dict]:
        return sym, compute_screen(screen_name, sym, force=force, market=market).to_dict()

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, sym): sym for sym in symbols}
        for fut in as_completed(futures):
            sym, result = fut.result()
            results[sym] = result
            done += 1
            if progress_cb:
                progress_cb(done, total)

    return [results[sym] for sym in symbols if sym in results]
