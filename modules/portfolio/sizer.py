# -*- coding: utf-8 -*-
"""
Position sizing: how many units of a stock to buy, respecting policy limits.

Constraints applied:
  - Max 8% of portfolio in any single stock
  - Max 15% of portfolio in any single sector
"""

from __future__ import annotations

from math import floor
from typing import Optional

from modules.market import get_section_data
from modules.portfolio.policy import _map_to_policy_sector, _safe_float
from modules.sharia import enrich_cached_sharia, load_cached_sharia

MAX_STOCK_PCT = 0.08
MAX_SECTOR_PCT = 0.15


def _market_snapshot(symbol: str) -> dict:
    data = get_section_data(symbol, "market")
    if data.get("error"):
        return {"symbol": symbol, "error": data["error"], "currentPrice": None}
    return {
        "symbol": symbol,
        "currentPrice": _safe_float(data.get("currentPrice")),
    }


def _get_sector(symbol: str, sharia_df) -> Optional[str]:
    """Look up policy sector for a symbol from Sharia cache."""
    if sharia_df is None or sharia_df.empty:
        return None
    rows = sharia_df[sharia_df["symbol"] == symbol]
    if rows.empty:
        return None
    row = rows.sort_values("report_period", ascending=False).iloc[0]
    return _map_to_policy_sector(row.get("industry"), row.get("sector"))


def compute_position_size(
    symbol: str,
    holdings: list[dict],
    sip_amount: float = 0.0,
) -> dict:
    """
    Compute how many units to buy for `symbol` given current holdings and
    an optional SIP/lump sum amount.

    holdings: list of dicts with keys symbol, units, price (optional)
    sip_amount: fresh capital available to deploy (0 = just report headroom)
    """
    # ── Load Sharia metadata ───────────────────────────────────────────────────
    sharia_df = load_cached_sharia()
    sharia_df = enrich_cached_sharia(sharia_df) if sharia_df is not None else None

    target_sector = _get_sector(symbol, sharia_df)

    # ── Fetch prices for all holdings + target symbol ─────────────────────────
    all_symbols = list({h["symbol"] for h in holdings} | {symbol})
    prices: dict[str, Optional[float]] = {}
    for sym in all_symbols:
        snap = _market_snapshot(sym)
        prices[sym] = snap.get("currentPrice")

    # Allow price overrides from holdings
    for h in holdings:
        if h.get("price"):
            prices[h["symbol"]] = _safe_float(h["price"])

    target_price = prices.get(symbol)
    if not target_price:
        return {"error": f"Could not fetch current price for {symbol}"}

    # ── Compute portfolio value ────────────────────────────────────────────────
    total_value = 0.0
    for h in holdings:
        p = prices.get(h["symbol"])
        if p:
            total_value += p * float(h.get("units") or 0)

    if total_value == 0:
        return {"error": "Portfolio value is zero — check holdings and prices"}

    # ── Current exposure to target stock ──────────────────────────────────────
    existing_units = sum(
        float(h.get("units") or 0)
        for h in holdings
        if h["symbol"] == symbol
    )
    existing_stock_value = existing_units * target_price

    # ── Current sector exposure ───────────────────────────────────────────────
    current_sector_value = 0.0
    if target_sector:
        for h in holdings:
            h_sector = _get_sector(h["symbol"], sharia_df)
            if h_sector == target_sector:
                p = prices.get(h["symbol"])
                if p:
                    current_sector_value += p * float(h.get("units") or 0)

    # ── Headroom calculation ──────────────────────────────────────────────────
    max_stock_value = total_value * MAX_STOCK_PCT
    max_sector_value = total_value * MAX_SECTOR_PCT

    stock_headroom = max(0.0, max_stock_value - existing_stock_value)
    sector_headroom = max(0.0, max_sector_value - current_sector_value)
    max_investable = min(stock_headroom, sector_headroom)

    binding = "stock_cap" if stock_headroom <= sector_headroom else "sector_cap"

    # ── Invest amount and units ───────────────────────────────────────────────
    warnings = []
    if max_investable == 0:
        warnings.append(
            f"{'Stock' if binding == 'stock_cap' else 'Sector'} already at maximum allocation"
        )
        invest_amount = 0.0
        suggested_units = 0
    elif sip_amount > 0:
        invest_amount = min(sip_amount, max_investable)
        if sip_amount > max_investable:
            warnings.append(
                f"SIP ₹{sip_amount:,.0f} exceeds headroom ₹{max_investable:,.0f} — "
                f"capped at headroom ({binding})"
            )
        suggested_units = floor(invest_amount / target_price)
        invest_amount = suggested_units * target_price  # actual spend
    else:
        invest_amount = max_investable
        suggested_units = floor(invest_amount / target_price)
        invest_amount = suggested_units * target_price

    return {
        "symbol": symbol,
        "current_price": target_price,
        "portfolio_value": round(total_value, 2),
        "sector": target_sector,
        "sector_current_pct": round(current_sector_value / total_value, 4),
        "sector_max_pct": MAX_SECTOR_PCT,
        "sector_headroom": round(sector_headroom, 2),
        "stock_current_pct": round(existing_stock_value / total_value, 4),
        "stock_max_pct": MAX_STOCK_PCT,
        "stock_headroom": round(stock_headroom, 2),
        "max_investable": round(max_investable, 2),
        "sip_amount": sip_amount,
        "invest_amount": round(invest_amount, 2),
        "suggested_units": suggested_units,
        "invest_value": round(suggested_units * target_price, 2),
        "binding_constraint": binding,
        "warnings": warnings,
    }
