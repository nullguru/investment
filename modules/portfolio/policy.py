# -*- coding: utf-8 -*-
"""
Policy-aware portfolio gap analysis.

Compares current holdings against the personal portfolio construction policy:
  - 55% large / 30% mid / 15% small cap
  - Max 15% per sector, 8% per stock
  - Target 15-18 stocks across 8+ sectors
  - Priority gaps: Auto, Specialty Chemicals
"""

from __future__ import annotations

from math import floor
from typing import Optional

from modules.market import get_section_data
from modules.sharia import enrich_cached_sharia, load_cached_sharia
from modules.universe.cap_tier import get_cap_tier_by_symbol

# ── Policy constants ─────────────────────────────────────────────────────────

CAP_TARGETS = {"large": 0.55, "mid": 0.30, "small": 0.15}

CONCENTRATION = {
    "max_sector_pct": 0.15,
    "max_stock_pct": 0.08,
    "target_stocks_min": 15,
    "target_stocks_max": 18,
    "hard_max_stocks": 20,
    "min_sectors": 8,
}

# Sectors in the policy target map with priority order
SECTOR_TARGETS = [
    {"name": "IT / Software",               "target_min": 0.12, "target_max": 0.15, "max_stocks": 3},
    {"name": "Pharma / Healthcare",         "target_min": 0.10, "target_max": 0.12},
    {"name": "FMCG / Consumer Staples",     "target_min": 0.08, "target_max": 0.10},
    {"name": "Industrial / Capital Goods",  "target_min": 0.10, "target_max": 0.12},
    {"name": "Auto / Auto Ancillary",       "target_min": 0.08, "target_max": 0.10, "priority": "high"},
    {"name": "Energy",                      "target_min": 0.07, "target_max": 0.10},
    {"name": "Consumer Discretionary",      "target_min": 0.08, "target_max": 0.10},
    {"name": "Specialty Chemicals",         "target_min": 0.05, "target_max": 0.08, "priority": "high"},
    {"name": "Healthcare Devices / Diagnostics", "target_min": 0.05, "target_max": 0.08},
]

# Maps yfinance industry keywords → policy sector name (case-insensitive substring)
INDUSTRY_TO_POLICY_SECTOR = {
    "Auto Manufacturers":    "Auto / Auto Ancillary",
    "Auto Components":       "Auto / Auto Ancillary",
    "Auto Parts":            "Auto / Auto Ancillary",
    "Motorcycles":           "Auto / Auto Ancillary",
    "Specialty Chemicals":   "Specialty Chemicals",
    "Chemicals":             "Specialty Chemicals",
    "Software":              "IT / Software",
    "Information Technology": "IT / Software",
    "Technology":            "IT / Software",
    "Drug Manufacturers":    "Pharma / Healthcare",
    "Pharmaceuticals":       "Pharma / Healthcare",
    "Biotechnology":         "Pharma / Healthcare",
    "Medical Devices":       "Healthcare Devices / Diagnostics",
    "Diagnostics":           "Healthcare Devices / Diagnostics",
    "Consumer Defensive":    "FMCG / Consumer Staples",
    "Household Products":    "FMCG / Consumer Staples",
    "Beverages":             "FMCG / Consumer Staples",
    "Personal Products":     "FMCG / Consumer Staples",
    "Industrial":            "Industrial / Capital Goods",
    "Machinery":             "Industrial / Capital Goods",
    "Electrical Equipment":  "Industrial / Capital Goods",
    "Capital Goods":         "Industrial / Capital Goods",
    "Gas":                   "Energy",
    "Oil":                   "Energy",
    "Utilities":             "Energy",
    "Consumer Cyclical":     "Consumer Discretionary",
    "Retail":                "Consumer Discretionary",
    "Apparel":               "Consumer Discretionary",
    "Leisure":               "Consumer Discretionary",
}


def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (f != f) else f  # NaN check
    except (TypeError, ValueError):
        return None


def _market_snapshot(symbol: str) -> dict:
    data = get_section_data(symbol, "market")
    if data.get("error"):
        return {"symbol": symbol, "error": data["error"], "currentPrice": None, "marketCap": None}
    return {
        "symbol": symbol,
        "currentPrice": _safe_float(data.get("currentPrice")),
        "marketCap": _safe_float(data.get("marketCap")),
        "vs200DMA": _safe_float(data.get("vs200DMA")),
        "fiftyTwoWeekHigh": _safe_float(data.get("fiftyTwoWeekHigh")),
    }


def _map_to_policy_sector(industry, sector) -> Optional[str]:
    """Map yfinance industry/sector string to a policy sector name."""
    ind = industry if isinstance(industry, str) else ""
    sec = sector if isinstance(sector, str) else ""
    for keyword, policy_sector in INDUSTRY_TO_POLICY_SECTOR.items():
        if ind and keyword.lower() in ind.lower():
            return policy_sector
        if sec and keyword.lower() in sec.lower():
            return policy_sector
    return None


def analyze_portfolio(holdings: list[dict]) -> dict:
    """
    Analyze holdings against the portfolio construction policy.

    holdings: list of dicts with keys: symbol, units, price (optional override)
    Returns a structured gap analysis dict.
    """
    if not holdings:
        return {"error": "No holdings provided"}

    # Load Sharia cache for sector/industry metadata
    sharia_df = load_cached_sharia()
    sharia_df = enrich_cached_sharia(sharia_df) if sharia_df is not None else None

    def _sharia_meta(symbol: str) -> dict:
        if sharia_df is None or sharia_df.empty:
            return {}
        rows = sharia_df[sharia_df["symbol"] == symbol]
        if rows.empty:
            return {}
        row = rows.sort_values("report_period", ascending=False).iloc[0]
        def _str_or_none(v):
            return v if isinstance(v, str) else None

        return {
            "industry": _str_or_none(row.get("industry")),
            "sector": _str_or_none(row.get("sector")),
            "sharia": _str_or_none(row.get("Sharia")),
            "market_cap_cached": _safe_float(row.get("market_cap")),
        }

    # ── Enrich each holding with live price + metadata ────────────────────────
    enriched = []
    for h in holdings:
        symbol = h["symbol"]
        units = float(h.get("units") or 0)
        price_override = _safe_float(h.get("price"))

        snap = _market_snapshot(symbol)
        price = price_override or snap.get("currentPrice")
        market_cap = snap.get("marketCap")
        meta = _sharia_meta(symbol)

        if not market_cap:
            market_cap = meta.get("market_cap_cached")

        cap_tier = get_cap_tier_by_symbol(symbol) or "unknown"
        policy_sector = _map_to_policy_sector(meta.get("industry"), meta.get("sector"))

        value = (price * units) if price else None
        enriched.append({
            "symbol": symbol,
            "units": units,
            "price": price,
            "value": value,
            "cap_tier": cap_tier,
            "industry": meta.get("industry"),
            "sector": meta.get("sector"),
            "policy_sector": policy_sector,
            "sharia": meta.get("sharia"),
            "price_missing": price is None,
        })

    # ── Compute total value ───────────────────────────────────────────────────
    valued = [h for h in enriched if h["value"] is not None]
    total_value = sum(h["value"] for h in valued)

    if total_value == 0:
        return {"error": "Could not compute portfolio value — all prices missing"}

    # ── Weights ───────────────────────────────────────────────────────────────
    for h in enriched:
        h["weight"] = (h["value"] / total_value) if h["value"] else None

    # Cap allocation
    cap_actual: dict[str, float] = {"large": 0.0, "mid": 0.0, "small": 0.0, "unknown": 0.0}
    for h in enriched:
        tier = h["cap_tier"]
        if h["weight"]:
            cap_actual[tier] = cap_actual.get(tier, 0.0) + h["weight"]

    cap_allocation = {}
    for tier, target in CAP_TARGETS.items():
        actual = cap_actual.get(tier, 0.0)
        gap = target - actual
        if actual > target + 0.02:
            status = "overweight"
        elif actual < target - 0.02:
            status = "underweight"
        else:
            status = "on_target"
        cap_allocation[tier] = {
            "actual": round(actual, 4),
            "target": target,
            "gap": round(gap, 4),
            "status": status,
        }

    # Sector weights
    sector_map: dict[str, dict] = {}
    for h in enriched:
        ps = h["policy_sector"] or "Unclassified"
        if ps not in sector_map:
            sector_map[ps] = {"sector": ps, "weight": 0.0, "stocks": 0, "symbols": []}
        if h["weight"]:
            sector_map[ps]["weight"] += h["weight"]
        sector_map[ps]["stocks"] += 1
        sector_map[ps]["symbols"].append(h["symbol"])

    # Sector flags
    for s in sector_map.values():
        s["weight"] = round(s["weight"], 4)
        flags = []
        if s["weight"] > CONCENTRATION["max_sector_pct"]:
            flags.append("overweight")
        # IT ceiling check
        target_def = next((t for t in SECTOR_TARGETS if t["name"] == s["sector"]), None)
        if target_def and target_def.get("max_stocks") and s["stocks"] >= target_def["max_stocks"]:
            flags.append("at_ceiling")
        s["flags"] = flags

    sector_weights = sorted(sector_map.values(), key=lambda x: -x["weight"])

    # Stock concentration flags
    stock_flags = []
    for h in enriched:
        if h["weight"] and h["weight"] > CONCENTRATION["max_stock_pct"]:
            stock_flags.append({
                "symbol": h["symbol"],
                "weight": round(h["weight"], 4),
                "flag": "exceeds_8pct_cap",
            })

    # ── Gap analysis ──────────────────────────────────────────────────────────
    covered_policy_sectors = {h["policy_sector"] for h in enriched if h["policy_sector"]}
    gaps = []
    for target_def in SECTOR_TARGETS:
        name = target_def["name"]
        current = sector_map.get(name, {})
        current_weight = current.get("weight", 0.0)
        current_stocks = current.get("stocks", 0)
        max_stocks = target_def.get("max_stocks")
        priority = target_def.get("priority", "normal")

        if name not in covered_policy_sectors:
            # Determine which cap tier to fill this sector in
            if name in ("Auto / Auto Ancillary",):
                cap_hint = "large"  # Maruti, Hero, Bajaj are large cap
            elif name in ("Specialty Chemicals",):
                cap_hint = "mid"
            else:
                cap_hint = "large"

            gaps.append({
                "sector": name,
                "cap_tier": cap_hint,
                "status": "missing",
                "priority": priority,
                "current_weight": 0.0,
                "target_min": target_def["target_min"],
                "target_max": target_def["target_max"],
            })
        elif current_weight < target_def["target_min"]:
            gaps.append({
                "sector": name,
                "cap_tier": "any",
                "status": "underweight",
                "priority": priority,
                "current_weight": round(current_weight, 4),
                "target_min": target_def["target_min"],
                "target_max": target_def["target_max"],
            })
        elif max_stocks and current_stocks >= max_stocks:
            gaps.append({
                "sector": name,
                "cap_tier": None,
                "status": "at_ceiling",
                "priority": "blocked",
                "current_weight": round(current_weight, 4),
                "target_min": target_def["target_min"],
                "target_max": target_def["target_max"],
            })

    # Sort gaps: high priority missing first, then underweight, then blocked
    priority_order = {"high": 0, "normal": 1, "blocked": 2}
    status_order = {"missing": 0, "underweight": 1, "at_ceiling": 2}
    gaps.sort(key=lambda g: (priority_order.get(g["priority"], 9), status_order.get(g["status"], 9)))

    # ── Action items ──────────────────────────────────────────────────────────
    action_items = []
    for g in gaps:
        if g["status"] in ("missing", "underweight") and g.get("cap_tier") != "blocked":
            action_items.append({
                "type": "add",
                "sector": g["sector"],
                "cap_tier": g["cap_tier"],
                "priority": g["priority"],
                "reason": f"Sector {'missing' if g['status'] == 'missing' else 'underweight'} — "
                          f"target {int(g['target_min']*100)}–{int(g['target_max']*100)}%, "
                          f"current {int(g['current_weight']*100)}%",
            })

    # ── Policy compliance check ───────────────────────────────────────────────
    total_stocks = len(enriched)
    total_sectors = len([s for s in sector_map if s != "Unclassified"])
    concentration_flags = (
        [f"{h['symbol']} exceeds 8% stock cap ({int(h['weight']*100)}%)" for h in stock_flags]
        + [f"{s['sector']} sector overweight ({int(s['weight']*100)}%)"
           for s in sector_weights if "overweight" in s["flags"]]
        + [f"{s['sector']} sector at stock ceiling ({s['stocks']} stocks)"
           for s in sector_weights if "at_ceiling" in s["flags"]]
    )
    policy_met = (
        not concentration_flags
        and total_sectors >= CONCENTRATION["min_sectors"]
        and all(c["status"] == "on_target" for c in cap_allocation.values())
        and not gaps
    )

    return {
        "summary": {
            "total_value": round(total_value, 2),
            "stock_count": total_stocks,
            "sector_count": total_sectors,
            "policy_met": policy_met,
            "missing_prices": [h["symbol"] for h in enriched if h["price_missing"]],
        },
        "cap_allocation": cap_allocation,
        "sector_weights": sector_weights,
        "stock_weights": [
            {"symbol": h["symbol"], "weight": round(h["weight"], 4), "cap_tier": h["cap_tier"],
             "policy_sector": h["policy_sector"], "value": round(h["value"], 2) if h["value"] else None}
            for h in sorted(enriched, key=lambda x: -(x["weight"] or 0))
        ],
        "concentration_flags": concentration_flags,
        "gaps": gaps,
        "action_items": action_items,
    }
