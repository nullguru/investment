# -*- coding: utf-8 -*-
"""
Personal Sharia index analysis.

Builds a benchmark-aware, long-term portfolio view using:
- current holdings (symbol + units, optional price override)
- latest cached Sharia status
- benchmark membership from local JSON definitions

Default behavior is conservative:
- only suggest exits for non-Sharia holdings
- use new money to move closer to the benchmark
- freeze fresh buying for compliant but off-benchmark names
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from core.config import DB_DIR
from modules.market import get_section_data
from modules.sharia import enrich_cached_sharia, format_date_ordinal, load_cached_sharia

BENCHMARKS_DIR = DB_DIR / "benchmarks"


def list_benchmarks() -> list[dict]:
    """List locally configured benchmarks."""
    out = []
    if not BENCHMARKS_DIR.exists():
        return out
    for fp in sorted(BENCHMARKS_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            out.append({
                "id": data.get("id") or fp.stem,
                "name": data.get("name") or fp.stem,
                "as_of": data.get("as_of"),
                "weight_method": data.get("weight_method", "proxy_market_cap"),
                "symbol_count": len(data.get("symbols", [])),
                "source": data.get("source", {}),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return out


def load_benchmark(benchmark_id: str) -> dict:
    """Load one benchmark definition."""
    fp = BENCHMARKS_DIR / f"{benchmark_id}.json"
    if not fp.exists():
        raise ValueError(f"Unknown benchmark: {benchmark_id}")
    data = json.loads(fp.read_text(encoding="utf-8"))
    if not data.get("symbols"):
        raise ValueError(f"Benchmark {benchmark_id} has no symbols")
    return data


def parse_holdings_text(raw: str) -> list[dict]:
    """Parse multiline holdings input: SYMBOL units [price]."""
    holdings: list[dict] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        normalized = line.replace(",", " ").replace(":", " ")
        parts = [p for p in normalized.split() if p]
        if len(parts) < 2:
            continue
        symbol = parts[0].strip().upper()
        try:
            units = float(parts[1])
        except ValueError:
            continue
        price = None
        if len(parts) >= 3:
            try:
                price = float(parts[2])
            except ValueError:
                price = None
        holdings.append({"symbol": symbol, "units": units, "price": price})
    return holdings


def parse_holdings_arg(raw: str) -> list[dict]:
    """Parse CLI holdings string: SYMBOL:units[:price],SYMBOL:units[:price]."""
    rows = []
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split(":") if p.strip()]
        if len(parts) < 2:
            continue
        symbol = parts[0].upper()
        try:
            units = float(parts[1])
        except ValueError:
            continue
        price = None
        if len(parts) >= 3:
            try:
                price = float(parts[2])
            except ValueError:
                price = None
        rows.append({"symbol": symbol, "units": units, "price": price})
    return rows


def _latest_sharia_rows() -> pd.DataFrame:
    cached = load_cached_sharia()
    if cached is None or cached.empty:
        return pd.DataFrame()
    df = enrich_cached_sharia(cached).copy()
    df["_rp_dt"] = pd.to_datetime(df["report_period"], errors="coerce")
    df = df.sort_values(["symbol", "_rp_dt"]).groupby("symbol", as_index=False).last()
    return df


def _resolve_symbol(symbol: str, known: set[str]) -> str | None:
    s = (symbol or "").strip().upper()
    if not s:
        return None
    if s in known:
        return s
    if "." not in s:
        for suffix in (".NS", ".BO"):
            candidate = s + suffix
            if candidate in known:
                return candidate
    return None


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        if pd.isna(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _market_snapshot(symbol: str, force: bool = False) -> dict:
    data = get_section_data(symbol, "market", force=force)
    if data.get("error"):
        return {"symbol": symbol, "error": data["error"]}
    return {
        "symbol": symbol,
        "currentPrice": _safe_float(data.get("currentPrice")),
        "vs200DMA": _safe_float(data.get("vs200DMA")),
        "fiftyTwoWeekHigh": _safe_float(data.get("fiftyTwoWeekHigh")),
        "fiftyTwoWeekLow": _safe_float(data.get("fiftyTwoWeekLow")),
        "marketCap": _safe_float(data.get("marketCap")),
    }


def _aggregate_holdings(holdings: list[dict], known_symbols: set[str]) -> tuple[list[dict], list[str]]:
    grouped: dict[str, dict] = {}
    missing: list[str] = []
    for row in holdings:
        resolved = _resolve_symbol(row.get("symbol"), known_symbols)
        if not resolved:
            missing.append(row.get("symbol", ""))
            continue
        current = grouped.setdefault(resolved, {
            "input_symbols": [],
            "symbol": resolved,
            "units": 0.0,
            "price_override": None,
        })
        current["input_symbols"].append(row.get("symbol"))
        current["units"] += float(row.get("units") or 0.0)
        if row.get("price") is not None:
            current["price_override"] = float(row["price"])
    return list(grouped.values()), missing


def analyze_personal_index(
    holdings: list[dict],
    benchmark_id: str = "nifty50",
    sip_amount: float = 0.0,
    strict_no_sell: bool = True,
    max_buy_suggestions: int = 10,
) -> dict:
    """Analyze a personal portfolio against a Sharia-filtered benchmark."""
    latest_df = _latest_sharia_rows()
    if latest_df.empty:
        return {
            "error": "No Sharia cache available. Compute or backfill data first.",
            "benchmark": benchmark_id,
            "holdings": [],
        }

    latest_by_symbol = {row["symbol"]: row for row in latest_df.to_dict("records")}
    known_symbols = set(latest_by_symbol)
    benchmark = load_benchmark(benchmark_id)

    benchmark_resolved = []
    benchmark_missing = []
    for sym in benchmark.get("symbols", []):
        resolved = _resolve_symbol(sym, known_symbols)
        if resolved:
            benchmark_resolved.append(resolved)
        else:
            benchmark_missing.append(sym)

    benchmark_rows = [latest_by_symbol[s] for s in benchmark_resolved]
    benchmark_compliant = [
        r for r in benchmark_rows
        if r.get("Sharia") == "Yes" and _safe_float(r.get("market_cap")) not in (None, 0.0)
    ]
    benchmark_target_cap = sum(_safe_float(r.get("market_cap")) or 0.0 for r in benchmark_compliant)
    target_weights = {
        r["symbol"]: (_safe_float(r.get("market_cap")) or 0.0) / benchmark_target_cap
        for r in benchmark_compliant
        if benchmark_target_cap > 0
    }

    aggregated, missing_symbols = _aggregate_holdings(holdings, known_symbols)

    holding_rows = []
    priced_value_total = 0.0
    for row in aggregated:
        sym = row["symbol"]
        latest = latest_by_symbol[sym]
        price_override = row.get("price_override")
        market = None if price_override is not None else _market_snapshot(sym)
        current_price = price_override if price_override is not None else market.get("currentPrice")
        price_source = "manual" if price_override is not None else ("market" if current_price is not None else "unavailable")
        value = None if current_price is None else round(row["units"] * current_price, 2)
        if value is not None:
            priced_value_total += value
        holding_rows.append({
            "symbol": sym,
            "name": latest.get("name") or sym,
            "input_symbols": row.get("input_symbols", []),
            "units": round(row["units"], 4),
            "price_override": price_override,
            "current_price": current_price,
            "price_source": price_source,
            "value": value,
            "Sharia": latest.get("Sharia") or "Unknown",
            "report_period": format_date_ordinal(latest.get("report_period")),
            "industry": latest.get("industry"),
            "sector": latest.get("sector"),
            "market_cap": latest.get("market_cap"),
            "benchmark_member": sym in benchmark_resolved,
            "benchmark_target_weight": target_weights.get(sym, 0.0),
            "benchmark_source": benchmark.get("name"),
            "vs200DMA": None if market is None else market.get("vs200DMA"),
            "market_error": None if market is None else market.get("error"),
        })

    current_weights = {
        row["symbol"]: ((row["value"] or 0.0) / priced_value_total if priced_value_total > 0 and row["value"] is not None else 0.0)
        for row in holding_rows
    }

    for row in holding_rows:
        current_weight = current_weights.get(row["symbol"], 0.0)
        target_weight = row["benchmark_target_weight"]
        gap_weight = target_weight - current_weight
        action = "Hold"
        rationale = "Keep monitoring."
        if row["Sharia"] == "No":
            action = "Exit / stop SIP"
            rationale = "Current holding is not Sharia compliant."
        elif row["Sharia"] == "Unknown":
            action = "Review / no new money"
            rationale = "Latest Sharia view is incomplete or unknown."
        elif row["benchmark_member"] and gap_weight > 0.0025:
            action = "Add on SIP / dips"
            rationale = "Compliant benchmark name is under target weight."
        elif row["benchmark_member"] and gap_weight < -0.0025:
            if strict_no_sell:
                action = "Hold / no new buys"
                rationale = "Over target, but no-sell mode keeps compliant holdings and redirects new money elsewhere."
            else:
                action = "Trim toward target"
                rationale = "Compliant benchmark name is above target weight."
        elif not row["benchmark_member"] and row["Sharia"] == "Yes":
            action = "Hold / no new buys" if strict_no_sell else "Reduce over time"
            rationale = "Compliant but outside the chosen benchmark."
        row["current_weight"] = current_weight
        row["weight_gap"] = gap_weight
        row["action"] = action
        row["rationale"] = rationale

    non_sharia_rows = [r for r in holding_rows if r["Sharia"] == "No"]
    unknown_rows = [r for r in holding_rows if r["Sharia"] == "Unknown"]
    compliant_rows = [r for r in holding_rows if r["Sharia"] == "Yes"]

    candidate_rows = []
    for sym, target_weight in target_weights.items():
        gap_weight = max(target_weight - current_weights.get(sym, 0.0), 0.0)
        if strict_no_sell and gap_weight <= 0:
            continue
        latest = latest_by_symbol[sym]
        candidate_rows.append({
            "symbol": sym,
            "name": latest.get("name") or sym,
            "target_weight": target_weight,
            "current_weight": current_weights.get(sym, 0.0),
            "gap_weight": gap_weight,
        })

    candidate_rows.sort(key=lambda r: (r["gap_weight"], r["target_weight"]), reverse=True)
    if not candidate_rows:
        candidate_rows = [
            {
                "symbol": sym,
                "name": latest_by_symbol[sym].get("name") or sym,
                "target_weight": target_weight,
                "current_weight": current_weights.get(sym, 0.0),
                "gap_weight": max(target_weight - current_weights.get(sym, 0.0), 0.0),
            }
            for sym, target_weight in sorted(target_weights.items(), key=lambda item: item[1], reverse=True)
        ]

    top_candidates = candidate_rows[:max_buy_suggestions]
    buy_weight_denominator = sum(r["gap_weight"] for r in top_candidates if r["gap_weight"] > 0)
    if buy_weight_denominator <= 0:
        buy_weight_denominator = sum(r["target_weight"] for r in top_candidates)

    buy_plan = []
    for row in top_candidates:
        market = _market_snapshot(row["symbol"])
        price = market.get("currentPrice")
        dip_candidate = market.get("vs200DMA") is not None and market.get("vs200DMA") < 0
        allocation_share = (
            (row["gap_weight"] / buy_weight_denominator)
            if buy_weight_denominator > 0 and row["gap_weight"] > 0
            else (row["target_weight"] / buy_weight_denominator if buy_weight_denominator > 0 else 0.0)
        )
        invest_amount = round(sip_amount * allocation_share, 2) if sip_amount > 0 else None
        suggested_units = round(invest_amount / price, 4) if invest_amount and price else None
        buy_plan.append({
            "symbol": row["symbol"],
            "name": row["name"],
            "target_weight": row["target_weight"],
            "current_weight": row["current_weight"],
            "gap_weight": row["gap_weight"],
            "allocation_share": allocation_share,
            "invest_amount": invest_amount,
            "current_price": price,
            "suggested_units": suggested_units,
            "dip_candidate": dip_candidate,
            "vs200DMA": market.get("vs200DMA"),
            "action": "Prioritize on dip" if dip_candidate else "Add on SIP",
            "market_error": market.get("error"),
        })

    buy_plan.sort(key=lambda r: (r["dip_candidate"], r["allocation_share"]), reverse=True)

    compliant_value = sum((r["value"] or 0.0) for r in compliant_rows)
    benchmark_value = sum((r["value"] or 0.0) for r in holding_rows if r["benchmark_member"] and r["Sharia"] == "Yes")
    off_benchmark_value = sum((r["value"] or 0.0) for r in holding_rows if not r["benchmark_member"] and r["Sharia"] == "Yes")
    non_sharia_value = sum((r["value"] or 0.0) for r in non_sharia_rows)
    missing_prices = [r["symbol"] for r in holding_rows if r["current_price"] is None]

    summary = {
        "benchmark": benchmark.get("name"),
        "benchmark_id": benchmark.get("id"),
        "benchmark_as_of": benchmark.get("as_of"),
        "benchmark_weight_method": benchmark.get("weight_method", "proxy_market_cap"),
        "strict_no_sell": strict_no_sell,
        "sip_amount": sip_amount,
        "holdings_count": len(holding_rows),
        "priced_holdings_count": len([r for r in holding_rows if r["current_price"] is not None]),
        "missing_symbol_count": len(missing_symbols),
        "missing_price_count": len(missing_prices),
        "compliant_count": len(compliant_rows),
        "non_compliant_count": len(non_sharia_rows),
        "unknown_count": len(unknown_rows),
        "total_value": round(priced_value_total, 2) if priced_value_total > 0 else None,
        "sharia_compliant_value_pct": (compliant_value / priced_value_total) if priced_value_total > 0 else None,
        "benchmark_aligned_value_pct": (benchmark_value / priced_value_total) if priced_value_total > 0 else None,
        "off_benchmark_value_pct": (off_benchmark_value / priced_value_total) if priced_value_total > 0 else None,
        "non_sharia_value_pct": (non_sharia_value / priced_value_total) if priced_value_total > 0 else None,
        "guidance": (
            "Exit non-Sharia holdings and redirect new money into compliant benchmark underweights."
            if non_sharia_rows else
            "Stay in no-sell mode for compliant names and use new SIP cash to close benchmark gaps."
        ),
    }

    return {
        "summary": summary,
        "benchmark": {
            "id": benchmark.get("id"),
            "name": benchmark.get("name"),
            "as_of": benchmark.get("as_of"),
            "source": benchmark.get("source", {}),
            "weight_method": benchmark.get("weight_method", "proxy_market_cap"),
            "symbols": benchmark.get("symbols", []),
            "resolved_symbol_count": len(benchmark_resolved),
            "missing_symbols": benchmark_missing,
            "compliant_constituent_count": len(benchmark_compliant),
        },
        "holdings": holding_rows,
        "buy_plan": buy_plan,
        "sell_plan": [
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "units": r["units"],
                "value": r["value"],
                "reason": "Current Sharia status is No.",
            }
            for r in non_sharia_rows
        ],
        "missing_symbols": missing_symbols,
        "missing_prices": missing_prices,
    }
