# -*- coding: utf-8 -*-
"""
Sharia-compliant candidate universe for a given sector + cap tier slot.

Usage:
    from modules.universe.suggest import suggest_candidates
    result = suggest_candidates(
        sector_keyword="Auto",
        cap_tier="large",
        exclude_symbols=["TCS.NS", "INFY.NS"],
    )
"""

from __future__ import annotations

from typing import Optional

from modules.market import get_section_data
from modules.sharia import enrich_cached_sharia, load_cached_sharia
from modules.universe.cap_tier import get_symbols_for_tier


def suggest_candidates(
    sector_keyword: str,
    cap_tier: str,
    exclude_symbols: Optional[list[str]] = None,
    force_sharia: bool = False,
    max_sector_lookups: int = 10,
    max_results: int = 30,
) -> dict:
    """
    Return Sharia-compliant candidates for a sector + cap tier slot.

    sector_keyword  – matched case-insensitively against industry AND sector columns
                      e.g. "Auto" matches "Auto Manufacturers", "Auto Components"
    cap_tier        – "large", "mid", or "small"
    exclude_symbols – symbols already owned (stripped before comparison)
    force_sharia    – if True, compute Sharia for uncached symbols on-demand
    """
    exclude = {s.upper() for s in (exclude_symbols or [])}

    # ── 1. Cap tier universe ──────────────────────────────────────────────────
    tier_symbols = get_symbols_for_tier(cap_tier)
    if not tier_symbols:
        return {
            "error": f"No symbols found for cap tier '{cap_tier}'. "
                     "Run: ./cli.py compute --missing to populate the Sharia cache.",
            "query": {"sector": sector_keyword, "cap_tier": cap_tier},
        }

    # ── 2. Load Sharia cache ──────────────────────────────────────────────────
    sharia_df = load_cached_sharia()
    if sharia_df is None or sharia_df.empty:
        return {
            "error": "Sharia cache is empty. Run: ./cli.py compute --portfolio",
            "query": {"sector": sector_keyword, "cap_tier": cap_tier},
        }
    sharia_df = enrich_cached_sharia(sharia_df)

    # Deduplicate: one row per symbol, most recent report period
    latest = (
        sharia_df
        .sort_values("report_period", ascending=False)
        .drop_duplicates(subset="symbol", keep="first")
        .set_index("symbol")
    )

    # ── 3. Filter to Sharia compliant ─────────────────────────────────────────
    kw_lower = sector_keyword.lower()

    candidates = []
    sharia_unknown = []
    sharia_no = []

    for sym in tier_symbols:
        if sym.upper() in exclude:
            continue

        if sym not in latest.index:
            if force_sharia:
                # Compute on demand
                from modules.sharia.service import compute_sharia_metrics
                _compute_and_refresh(sym)
                sharia_df2 = load_cached_sharia()
                if sharia_df2 is not None:
                    sharia_df = enrich_cached_sharia(sharia_df2)
                    latest = (
                        sharia_df
                        .sort_values("report_period", ascending=False)
                        .drop_duplicates(subset="symbol", keep="first")
                        .set_index("symbol")
                    )
            if sym not in latest.index:
                sharia_unknown.append(sym)
                continue

        row = latest.loc[sym]
        sharia_status = row.get("Sharia", "Unknown")

        if sharia_status != "Yes":
            sharia_no.append(sym)
            continue

        # ── 4. Sector filter ──────────────────────────────────────────────────
        industry = row.get("industry") or ""
        sector = row.get("sector") or ""

        industry_match = kw_lower in industry.lower()
        sector_match = kw_lower in sector.lower()

        if not industry_match and not sector_match:
            # For unknown industry in cache, optionally do a live lookup
            if not industry and not sector and len(candidates) + len(sharia_unknown) < max_sector_lookups:
                live = _fetch_overview(sym)
                industry = live.get("industry", "")
                sector = live.get("sector", "")
                industry_match = kw_lower in industry.lower()
                sector_match = kw_lower in sector.lower()

            if not industry_match and not sector_match:
                continue

        candidates.append({
            "symbol": sym,
            "industry": industry or None,
            "sector": sector or None,
            "cap_tier": cap_tier,
            "market_cap": _safe_float(row.get("market_cap")),
            "sharia": sharia_status,
            "sharia_period": row.get("report_period"),
        })

    # Sort by market cap descending
    candidates.sort(key=lambda c: -(c["market_cap"] or 0))
    candidates = candidates[:max_results]

    result = {
        "query": {"sector": sector_keyword, "cap_tier": cap_tier},
        "candidates": candidates,
        "candidate_count": len(candidates),
        "excluded_count": len([s for s in tier_symbols if s.upper() in exclude]),
        "sharia_no_count": len(sharia_no),
        "sharia_unknown_count": len(sharia_unknown),
    }

    if sharia_unknown:
        result["note"] = (
            f"{len(sharia_unknown)} {cap_tier}-cap stocks not yet Sharia-screened. "
            "Run: ./cli.py compute --missing to screen them."
        )

    return result


def _safe_float(v):
    try:
        f = float(v)
        return None if (f != f) else f
    except (TypeError, ValueError):
        return None


def _fetch_overview(symbol: str) -> dict:
    data = get_section_data(symbol, "overview")
    return {
        "industry": data.get("industry", ""),
        "sector": data.get("sector", ""),
    }


def _compute_and_refresh(symbol: str) -> None:
    from modules.sharia.service import compute_sharia_metrics
    from modules.sharia.data import load_cached_sharia, save_sharia_cache
    import pandas as pd

    new_rows = compute_sharia_metrics([symbol])
    if not new_rows:
        return
    existing = load_cached_sharia()
    new_df = pd.DataFrame(new_rows)
    if existing is not None and not existing.empty:
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    save_sharia_cache(combined)
