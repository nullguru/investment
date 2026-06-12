# -*- coding: utf-8 -*-
"""
Portfolio performance vs benchmarks (ballpark tier).

Compares simple cost-basis return (avg buy price × units vs live price) against:
  - Indian indices (Nifty 50/100/500, Sensex)
  - Assumed India CPI inflation
  - USD-real return (FX-adjusted using USDINR at anchor vs today)

Requires an anchor date (invested_since). Per-lot buy dates / XIRR are Phase 2.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yfinance as yf

from core.config import DB_DIR
from modules.market import get_section_data

INDICES_PATH = DB_DIR / "performance" / "indices.json"
FX_TICKER = "USDINR=X"


def load_performance_indices() -> dict:
    """Load index ticker definitions and inflation assumption."""
    if not INDICES_PATH.exists():
        return {"inflation": {"annual_pct": 6.0}, "indices": []}
    try:
        return json.loads(INDICES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"inflation": {"annual_pct": 6.0}, "indices": []}


def list_performance_benchmarks() -> list[dict]:
    """Return selectable performance benchmarks (indices + inflation)."""
    cfg = load_performance_indices()
    out = []
    for row in cfg.get("indices", []):
        out.append({
            "id": row["id"],
            "name": row.get("name", row["id"]),
            "ticker": row.get("ticker"),
            "type": "index",
        })
    infl = cfg.get("inflation") or {}
    if infl:
        out.append({
            "id": infl.get("id", "inflation"),
            "name": infl.get("name", "Inflation"),
            "type": "inflation",
            "annual_pct": infl.get("annual_pct", 6.0),
        })
    return out


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _parse_date(value: str | None, default: date | None = None) -> date:
    if not value:
        if default is None:
            raise ValueError("anchor_date is required")
        return default
    text = str(value).strip()[:10]
    return datetime.strptime(text, "%Y-%m-%d").date()


def _period_years(start: date, end: date) -> float:
    return max((end - start).days, 1) / 365.25


def _fetch_closes(ticker: str, start: date, end: date) -> list[tuple[date, float]]:
    """Daily closes between start and end (inclusive), sorted by date."""
    try:
        hist = yf.Ticker(ticker).history(
            start=(start - timedelta(days=14)).isoformat(),
            end=(end + timedelta(days=2)).isoformat(),
            interval="1d",
        )
    except Exception:
        return []
    if hist is None or hist.empty:
        return []
    out: list[tuple[date, float]] = []
    for ts, row in hist.iterrows():
        close = _safe_float(row.get("Close"))
        if close is None:
            continue
        d = ts.date() if hasattr(ts, "date") else datetime.fromisoformat(str(ts)[:10]).date()
        out.append((d, close))
    out.sort(key=lambda x: x[0])
    return out


def _close_on_or_before(closes: list[tuple[date, float]], target: date) -> float | None:
    price = None
    for d, c in closes:
        if d <= target:
            price = c
        else:
            break
    return price


def _index_return_pct(ticker: str, anchor: date, as_of: date) -> dict:
    closes = _fetch_closes(ticker, anchor, as_of)
    if not closes:
        return {"return_pct": None, "error": f"No price history for {ticker}"}
    start_px = _close_on_or_before(closes, anchor)
    end_px = closes[-1][1]
    if start_px is None or not start_px:
        return {"return_pct": None, "error": f"No price on or before {anchor} for {ticker}"}
    ret = (end_px / start_px - 1.0) * 100.0
    return {
        "return_pct": round(ret, 2),
        "start_price": round(start_px, 4),
        "end_price": round(end_px, 4),
        "start_date_used": next(d.isoformat() for d, _ in closes if d <= anchor),
        "end_date_used": closes[-1][0].isoformat(),
    }


def _inflation_return_pct(annual_pct: float, years: float) -> float:
    return round(((1.0 + annual_pct / 100.0) ** years - 1.0) * 100.0, 2)


def _market_key(symbol: str, holding_markets: dict[str, str] | None) -> str:
    sym = symbol.upper()
    markets = holding_markets or {}
    return "us" if markets.get(sym, markets.get(symbol, "IN")) == "US" else "india"


def _live_price(symbol: str, market: str) -> float | None:
    data = get_section_data(symbol, "market", market=market)
    if data.get("error"):
        return None
    return _safe_float(data.get("currentPrice"))


def compute_portfolio_performance(
    holdings: list[dict],
    anchor_date: str | None = None,
    benchmark_ids: list[str] | None = None,
    holding_markets: dict[str, str] | None = None,
) -> dict:
    """
    Compare portfolio simple return vs benchmarks over [anchor_date, today].

    holdings: [{symbol, units, price?}] — price = avg buy in native currency (INR or USD).
    holding_markets: {SYMBOL: "IN"|"US"}
    """
    if not holdings:
        return {"error": "No holdings provided"}

    default_anchor = date.today() - timedelta(days=365)
    try:
        anchor = _parse_date(anchor_date, default=default_anchor)
    except ValueError as e:
        return {"error": str(e)}

    as_of = date.today()
    if anchor >= as_of:
        return {"error": "anchor_date must be before today"}

    years = _period_years(anchor, as_of)

    # FX
    fx_closes = _fetch_closes(FX_TICKER, anchor, as_of)
    usd_inr_anchor = _close_on_or_before(fx_closes, anchor)
    usd_inr_now = fx_closes[-1][1] if fx_closes else None
    rupee_dep_pct = None
    if usd_inr_anchor and usd_inr_now and usd_inr_anchor > 0:
        rupee_dep_pct = round((usd_inr_now / usd_inr_anchor - 1.0) * 100.0, 2)

    cost_inr = value_inr = 0.0
    cost_usd = value_usd = 0.0
    holdings_priced = 0
    missing_price: list[str] = []
    missing_quote: list[str] = []
    holding_details: list[dict] = []

    for row in holdings:
        sym = (row.get("symbol") or "").strip().upper()
        units = _safe_float(row.get("units"))
        buy = _safe_float(row.get("price"))
        if not sym or not units or units <= 0:
            continue
        market = _market_key(sym, holding_markets)
        is_us = market == "us"

        current = _live_price(sym, market)
        detail: dict[str, Any] = {
            "symbol": sym,
            "market": "US" if is_us else "IN",
            "units": units,
            "avg_buy": buy,
            "current_price": current,
        }

        if buy is None or buy <= 0:
            missing_price.append(sym)
            holding_details.append({**detail, "included": False, "reason": "no_avg_buy_price"})
            continue

        if current is None:
            missing_quote.append(sym)
            holding_details.append({**detail, "included": False, "reason": "no_live_price"})
            continue

        holdings_priced += 1
        cb_native = units * buy
        cv_native = units * current
        pnl_native = cv_native - cb_native
        pnl_pct = (pnl_native / cb_native * 100.0) if cb_native else None

        if is_us:
            cost_usd += cb_native
            value_usd += cv_native
            if usd_inr_anchor:
                cost_inr += cb_native * usd_inr_anchor
            if usd_inr_now:
                value_inr += cv_native * usd_inr_now
        else:
            cost_inr += cb_native
            value_inr += cv_native
            if usd_inr_anchor:
                cost_usd += cb_native / usd_inr_anchor
            if usd_inr_now:
                value_usd += cv_native / usd_inr_now

        holding_details.append({
            **detail,
            "included": True,
            "cost_basis_native": round(cb_native, 2),
            "current_value_native": round(cv_native, 2),
            "return_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
        })

    warnings: list[str] = []
    if missing_price:
        warnings.append(f"No avg buy price for: {', '.join(missing_price)}")
    if missing_quote:
        warnings.append(f"No live price for: {', '.join(missing_quote)}")
    if holdings_priced == 0:
        return {
            "error": "Need at least one holding with avg buy price and live quote",
            "anchor_date": anchor.isoformat(),
            "as_of_date": as_of.isoformat(),
            "warnings": warnings,
            "holdings_missing_price": missing_price,
            "holdings_missing_quote": missing_quote,
        }

    return_inr = (value_inr - cost_inr) / cost_inr * 100.0 if cost_inr > 0 else None
    return_usd = (value_usd - cost_usd) / cost_usd * 100.0 if cost_usd > 0 else None

    cfg = load_performance_indices()
    selected = set(benchmark_ids) if benchmark_ids else None
    benchmarks_out: list[dict] = []

    for idx in cfg.get("indices", []):
        bid = idx["id"]
        if selected is not None and bid not in selected:
            continue
        ticker = idx.get("ticker")
        if not ticker:
            continue
        bench = _index_return_pct(ticker, anchor, as_of)
        b_ret = bench.get("return_pct")
        alpha = round(return_inr - b_ret, 2) if return_inr is not None and b_ret is not None else None
        benchmarks_out.append({
            "id": bid,
            "name": idx.get("name", bid),
            "type": "index",
            "ticker": ticker,
            "return_pct": b_ret,
            "alpha_vs_portfolio_inr_pct": alpha,
            **{k: v for k, v in bench.items() if k not in ("return_pct",)},
        })

    infl_cfg = cfg.get("inflation") or {}
    infl_id = infl_cfg.get("id", "inflation")
    if selected is None or infl_id in selected:
        annual = float(infl_cfg.get("annual_pct", 6.0))
        infl_ret = _inflation_return_pct(annual, years)
        alpha_infl = round(return_inr - infl_ret, 2) if return_inr is not None else None
        benchmarks_out.append({
            "id": infl_id,
            "name": infl_cfg.get("name", "Inflation"),
            "type": "inflation",
            "annual_pct": annual,
            "return_pct": infl_ret,
            "alpha_vs_portfolio_inr_pct": alpha_infl,
            "note": infl_cfg.get("note"),
        })

    return {
        "anchor_date": anchor.isoformat(),
        "as_of_date": as_of.isoformat(),
        "period_days": (as_of - anchor).days,
        "period_years": round(years, 3),
        "portfolio": {
            "cost_basis_inr": round(cost_inr, 2),
            "current_value_inr": round(value_inr, 2),
            "return_pct_inr": round(return_inr, 2) if return_inr is not None else None,
            "cost_basis_usd": round(cost_usd, 2),
            "current_value_usd": round(value_usd, 2),
            "return_pct_usd": round(return_usd, 2) if return_usd is not None else None,
            "holdings_priced": holdings_priced,
            "holdings_total": len(holdings),
            "holdings_missing_price": missing_price,
            "holdings_missing_quote": missing_quote,
            "holdings": holding_details,
        },
        "fx": {
            "ticker": FX_TICKER,
            "usd_inr_anchor": round(usd_inr_anchor, 4) if usd_inr_anchor else None,
            "usd_inr_now": round(usd_inr_now, 4) if usd_inr_now else None,
            "rupee_depreciation_pct": rupee_dep_pct,
            "anchor_date_used": anchor.isoformat(),
        },
        "benchmarks": benchmarks_out,
        "warnings": warnings,
        "method": "simple_cost_basis",
        "method_note": (
            "Portfolio return = (current value − cost basis) / cost basis using avg buy prices. "
            "USD-real return converts INR holdings via USDINR at anchor vs today. "
            "Not XIRR — add per-lot dates later for money-weighted returns."
        ),
    }
