# -*- coding: utf-8 -*-
"""
FastAPI backend: serves API and static frontend.
Uses modules/ for all domain logic.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import math
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import DB_DIR, get_config
from core.cache import get_staleness, mark_refreshed

from modules.sharia import (
    ShariaStatus,
    is_industry_compliant,
    compute_sharia_metrics,
    SHARIA_TABLE_COLUMNS,
    DEFAULT_PORTFOLIO,
    DEFAULT_PORTFOLIO_MAP,
    load_cached_sharia,
    save_sharia_cache,
    enrich_cached_sharia,
    effective_sharia,
    format_date_ordinal,
    get_metrics_df_for_counts,
    get_report_period_options,
    parse_portfolio_symbols,
    resolve_search_to_ticker,
)
from modules.universe import load_universe
from modules.market import get_section_data as yf_get_section
from modules.portfolio import analyze_personal_index, list_benchmarks, load_benchmark, parse_holdings_text
from modules.quality import (
    compute_quality_score,
    batch_compute_quality,
    load_quality_cache,
)

# ----- Settings (JSON in db/) -----
SETTINGS_PATH = DB_DIR / "settings.json"

# ----- Watchlist (JSON in db/) -----
WATCHLIST_PATH = DB_DIR / "watchlist.json"

DEFAULT_SETTINGS = {
    "tableColumns": {},
    "period": "31st March 2025",
    "market": "india",
    "portfolioSymbolsText": "TCS\nINFY\nHCLTECH",
    "compareSymbolsText": "",
    "watchlistText": "",
    "personalIndexHoldingsText": "TCS 10\nINFY 8\nHCLTECH 6",
    "personalIndexBenchmark": "nifty50",
    "personalIndexSipAmount": 0.0,
    "personalIndexStrictNoSell": True,
    "computeN": 50,
    "computeWorkers": 5,
}

# Default portfolio text per market (for first-time settings)
DEFAULT_PORTFOLIO_TEXT = {
    "india": "TCS\nINFY\nHCLTECH",
    "us": "AAPL\nMSFT\nGOOGL",
}


def get_universe(market: str = "india"):
    return load_universe(market=market)


def get_cached_sharia(market: str = "india"):
    df = load_cached_sharia(market=market)
    if df is not None and len(df) > 0:
        df = enrich_cached_sharia(df)
        try:
            save_sharia_cache(df, market=market)
        except Exception:
            pass
    return df if df is not None and len(df) > 0 else None


def _sanitize(obj):
    """Recursively replace nan/inf/-inf with None so FastAPI can serialize the response."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj




# Ensure config/cache dir exists
get_config()


def _load_settings() -> dict:
    """Load settings from db/settings.json."""
    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        out = DEFAULT_SETTINGS.copy()
        for k in DEFAULT_SETTINGS:
            if k in data:
                out[k] = data[k]
        return out
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def _save_settings(settings: dict) -> None:
    """Persist settings to db/settings.json."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    to_save = {k: settings.get(k, v) for k, v in DEFAULT_SETTINGS.items()}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2)


def _load_watchlist() -> list[str]:
    """Load watchlist symbols from db/watchlist.json."""
    if not WATCHLIST_PATH.exists():
        return []
    try:
        data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        return [str(s) for s in data.get("symbols", []) if s]
    except (json.JSONDecodeError, OSError):
        return []


def _save_watchlist(symbols: list[str]) -> None:
    """Persist watchlist to db/watchlist.json."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    # Deduplicate, preserve order
    seen: set[str] = set()
    unique = []
    for s in symbols:
        s = s.strip().upper()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    WATCHLIST_PATH.write_text(json.dumps({"symbols": unique}, indent=2), encoding="utf-8")


app = FastAPI(title="Investment Platform API")

# Mount frontend (static files)
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
async def root():
    """Serve the SPA."""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Frontend not found. Place index.html in frontend/."}


# ----- API -----

@app.get("/api/config")
def api_config():
    cfg = get_config()
    return {k: str(v) if hasattr(v, "__fspath__") else v for k, v in cfg.items()}


class SettingsBody(BaseModel):
    tableColumns: dict = {}
    shariaVisibleColumns: dict = {}  # legacy, migrated to tableColumns on frontend
    period: str = "31st March 2025"
    market: str = "india"
    portfolioSymbolsText: str = "TCS\nINFY\nHCLTECH"
    compareSymbolsText: str = ""
    watchlistText: str = ""
    personalIndexHoldingsText: str = "TCS 10\nINFY 8\nHCLTECH 6"
    personalIndexBenchmark: str = "nifty50"
    personalIndexSipAmount: float = 0.0
    personalIndexStrictNoSell: bool = True
    computeN: int = 50
    computeWorkers: int = 5


@app.get("/api/settings")
def api_get_settings():
    return _load_settings()


@app.put("/api/settings")
def api_put_settings(body: SettingsBody):
    settings = body.model_dump()
    _save_settings(settings)
    return {"ok": True}


@app.get("/api/personal-index/options")
def api_personal_index_options():
    """Benchmarks and example holdings syntax for the personal Sharia index tool."""
    return {
        "benchmarks": list_benchmarks(),
        "example_lines": [
            "TCS 10",
            "INFY 8",
            "MARUTI.NS 2 11850",
        ],
        "notes": [
            "Format each line as SYMBOL units [optional_price].",
            "If no price is supplied, the API tries to fetch the current market price.",
            "Benchmark weights are proxy market-cap weights among currently Sharia-compliant benchmark constituents.",
        ],
    }


class PersonalIndexBody(BaseModel):
    holdings_text: str = ""
    benchmark: str = "nifty50"
    sip_amount: float = 0.0
    strict_no_sell: bool = True
    max_buy_suggestions: int = 10


@app.post("/api/personal-index/analyze")
def api_personal_index_analyze(body: PersonalIndexBody):
    """Analyze a holdings list against a Sharia-filtered benchmark."""
    holdings = parse_holdings_text(body.holdings_text)
    if not holdings:
        raise HTTPException(400, "Provide holdings as lines like 'TCS 10' or 'MARUTI.NS 2 11850'")
    try:
        result = analyze_personal_index(
            holdings=holdings,
            benchmark_id=body.benchmark,
            sip_amount=body.sip_amount,
            strict_no_sell=body.strict_no_sell,
            max_buy_suggestions=body.max_buy_suggestions,
        )
        return _sanitize(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/universe")
def api_universe(market: str = Query("india")):
    tickers, exchange_map = get_universe(market=market)
    return {"tickers": tickers, "exchange_map": exchange_map}


@app.get("/api/report-periods")
def api_report_periods():
    cached = get_cached_sharia()
    return get_report_period_options(cached)


@app.get("/api/counts")
def api_counts(period: str = Query("31st March 2025"), market: str = Query("india")):
    cached = get_cached_sharia(market=market)
    tickers, _ = get_universe(market=market)
    total_universe = len(tickers)

    # How many universe symbols have ANY data in cache (period-agnostic)
    tickers_set = set(tickers)
    ever_screened = 0
    if cached is not None and not cached.empty:
        ever_screened = len(tickers_set & set(cached["symbol"].unique()))
    never_screened = total_universe - ever_screened

    metrics_df = get_metrics_df_for_counts(cached, period)
    if metrics_df is None or metrics_df.empty:
        return {
            "total_universe": total_universe,
            "compliant": 0,
            "non_compliant": 0,
            "unknown": 0,
            "n_with_data": 0,
            "never_screened": never_screened,
            "missing_for_period": ever_screened,
        }
    # Only count universe symbols
    metrics_df = metrics_df[metrics_df["symbol"].isin(tickers_set)]
    n_with_data = len(metrics_df)
    compliant = int((metrics_df["Sharia"] == ShariaStatus.YES.value).sum())
    non_compliant = int((metrics_df["Sharia"] == ShariaStatus.NO.value).sum())
    unknown = int((metrics_df["Sharia"] == ShariaStatus.UNKNOWN.value).sum())
    # Screened at least once but no row for selected period
    missing_for_period = ever_screened - n_with_data if period != "All periods" else 0
    return {
        "total_universe": total_universe,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "unknown": unknown,
        "n_with_data": n_with_data,
        "never_screened": never_screened,
        "missing_for_period": max(0, missing_for_period),
    }


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame to list of dicts, NaN/Inf -> None, dates as ISO string."""
    if df is None or df.empty:
        return []
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].astype(str)
    df = df.replace({pd.NA: None, np.nan: None})
    df = df.replace([np.inf, -np.inf], None)
    records = df.to_dict("records")
    def _json_safe(v):
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if hasattr(v, "item"):
            x = v.item()
            return None if isinstance(x, float) and (math.isnan(x) or math.isinf(x)) else x
        return v
    return [{k: _json_safe(v) for k, v in row.items()} for row in records]


@app.get("/api/sharia")
def api_sharia(period: str = Query("31st March 2025"), market: str = Query("india")):
    """All stocks with Sharia data (optionally filtered by period)."""
    cached = get_cached_sharia(market=market)
    _, exchange_map = get_universe(market=market)
    if cached is None:
        return {"rows": []}
    df = cached.copy()
    df["exchange"] = df["symbol"].map(exchange_map)
    if "report_period" not in df.columns:
        df["report_period"] = None
    if "industry_compliant" not in df.columns:
        df["industry_compliant"] = df.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    df["Sharia"] = df.apply(
        lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
    )
    if period != "All periods":
        df = df[df["report_period"].map(format_date_ordinal) == period]
    df["report_period"] = df["report_period"].map(
        lambda x: format_date_ordinal(x) if pd.notna(x) and x else ""
    )
    cols = [c for c in SHARIA_TABLE_COLUMNS if c in df.columns]
    out = df[cols]
    return {"rows": _df_to_records(out)}


@app.get("/api/sharia-compliant")
def api_sharia_compliant(period: str = Query("31st March 2025"), market: str = Query("india")):
    """Only Sharia-compliant stocks."""
    cached = get_cached_sharia(market=market)
    _, exchange_map = get_universe(market=market)
    if cached is None:
        return {"rows": []}
    df = cached.copy()
    df["exchange"] = df["symbol"].map(exchange_map)
    if "industry_compliant" not in df.columns:
        df["industry_compliant"] = df.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    df["Sharia"] = df.apply(
        lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
    )
    df = df[df["Sharia"] == ShariaStatus.YES.value]
    if period != "All periods":
        df = df[df["report_period"].map(format_date_ordinal) == period]
    df["report_period"] = df["report_period"].map(
        lambda x: format_date_ordinal(x) if pd.notna(x) and x else ""
    )
    cols = [c for c in SHARIA_TABLE_COLUMNS if c in df.columns]
    return {"rows": _df_to_records(df[cols])}


@app.get("/api/symbol/{symbol}")
def api_symbol(symbol: str, period: str | None = Query(None), market: str = Query("india")):
    """Single symbol overview (latest row or for period)."""
    cached = get_cached_sharia(market=market)
    if cached is None:
        raise HTTPException(404, "No Sharia data")
    df = cached[cached["symbol"] == symbol]
    if df.empty:
        raise HTTPException(404, f"Symbol {symbol} not in cache")
    if period and period != "All periods":
        df = df[df["report_period"].map(format_date_ordinal) == period]
    row = df.sort_values("report_period").iloc[-1].to_dict()
    if "industry_compliant" not in row or pd.isna(row.get("industry_compliant")):
        row["industry_compliant"] = is_industry_compliant(row.get("industry"), row.get("sector"))
    if "Sharia" not in row or pd.isna(row.get("Sharia")):
        row["Sharia"] = effective_sharia(row.get("compliant"), row.get("industry_compliant"))
    for k, v in list(row.items()):
        if pd.isna(v):
            row[k] = None
        elif hasattr(v, "item"):
            row[k] = v.item() if hasattr(v, "item") else v
    return row


@app.get("/api/symbol/{symbol}/periods")
def api_symbol_periods(symbol: str, market: str = Query("india")):
    """All cached period rows for a symbol."""
    cached = get_cached_sharia(market=market)
    if cached is None:
        return {"rows": []}
    df = cached[cached["symbol"] == symbol].copy()
    if df.empty:
        return {"rows": []}
    df = df.sort_values("report_period")
    if "industry_compliant" not in df.columns:
        df["industry_compliant"] = df.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    df["Sharia"] = df.apply(
        lambda r: effective_sharia(r.get("compliant"), r.get("industry_compliant")), axis=1
    )
    df["report_period"] = df["report_period"].map(
        lambda x: format_date_ordinal(x) if pd.notna(x) and x else ""
    )
    cols = [c for c in ["report_period", "period_type", "Sharia", "debt_to_equity_ratio",
            "cash_to_assets_pct", "other_revenue_to_revenue_pct", "receivables_to_assets_pct",
            "total_assets", "total_revenue", "market_cap"] if c in df.columns]
    return {"rows": _df_to_records(df[cols])}


@app.get("/api/symbol/{symbol}/section/{section}")
def api_symbol_section(symbol: str, section: str, force: bool = Query(False), market: str = Query("india")):
    """Fetch yfinance data for a symbol and section."""
    return yf_get_section(symbol, section, force=force, market=market)


@app.get("/api/symbol/{symbol}/metrics/history")
def api_symbol_metrics_history(symbol: str, market: str = Query("india")):
    """Multi-year financial metrics timeseries for chart rendering."""
    from modules.market.yf import get_metrics_history
    data = get_metrics_history(symbol, market=market)
    return _sanitize(data)


@app.get("/api/symbol/{symbol}/price/history")
def api_symbol_price_history(symbol: str, market: str = Query("india")):
    """2-year daily price, volume, 50 DMA, 200 DMA for charting."""
    from modules.market.yf import get_price_history
    data = get_price_history(symbol, market=market)
    return _sanitize(data)


@app.get("/api/symbol/{symbol}/research")
def api_symbol_research_all(symbol: str):
    """All research sections for a symbol."""
    from modules.research import load_research
    data = load_research(symbol)
    if not data:
        return {"sections": {}}
    return {"sections": data}


@app.get("/api/symbol/{symbol}/research/{section}")
def api_symbol_research_section(symbol: str, section: str):
    """One research section for a symbol."""
    from modules.research import load_research, RESEARCH_SECTIONS
    if section not in RESEARCH_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}. Valid: {RESEARCH_SECTIONS}")
    data = load_research(symbol, section)
    if not data:
        return {"error": "not_found", "section": section, "symbol": symbol}
    return data


@app.put("/api/symbol/{symbol}/research/{section}")
def api_symbol_research_put(symbol: str, section: str, body: dict):
    """Store one research section for a symbol."""
    from modules.research import save_research_section, RESEARCH_SECTIONS
    if section not in RESEARCH_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}. Valid: {RESEARCH_SECTIONS}")
    # Ensure envelope has required fields
    body.setdefault("section", section)
    body.setdefault("symbol", symbol)
    save_research_section(symbol, section, body)
    return {"status": "ok", "section": section, "symbol": symbol}


@app.get("/api/symbol/{symbol}/research/{section}/versions")
def api_symbol_research_versions(symbol: str, section: str):
    """List historical versions for a research section (newest first)."""
    from modules.research import load_research_versions, RESEARCH_SECTIONS
    if section not in RESEARCH_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}")
    versions = load_research_versions(symbol, section)
    # Return lightweight summary (no full data payload, just metadata)
    summary = [
        {"idx": i, "updated_at": v.get("updated_at"), "symbol": v.get("symbol", symbol)}
        for i, v in enumerate(versions)
    ]
    return {"versions": summary}


@app.delete("/api/symbol/{symbol}/research/{section}/versions/{version_idx}")
def api_symbol_research_version_delete(symbol: str, section: str, version_idx: int):
    """Delete a historical version by index (0 = newest historical)."""
    from modules.research import delete_research_version, RESEARCH_SECTIONS
    if section not in RESEARCH_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}")
    ok = delete_research_version(symbol, section, version_idx)
    if not ok:
        raise HTTPException(404, "Version not found")
    return {"status": "deleted", "idx": version_idx}


@app.post("/api/symbol/{symbol}/research/{section}/versions/{version_idx}/restore")
def api_symbol_research_version_restore(symbol: str, section: str, version_idx: int):
    """Restore a historical version to current."""
    from modules.research import restore_research_version, RESEARCH_SECTIONS
    if section not in RESEARCH_SECTIONS:
        raise HTTPException(400, f"Invalid section: {section}")
    envelope = restore_research_version(symbol, section, version_idx)
    if not envelope:
        raise HTTPException(404, "Version not found")
    return {"status": "restored", "envelope": envelope}


@app.get("/api/resolve")
def api_resolve(q: str = Query(""), market: str = Query("india")):
    """Resolve search query to ticker (e.g. TCS -> TCS.NS for India, AAPL -> AAPL for US)."""
    tickers, _ = get_universe(market=market)
    ticker = resolve_search_to_ticker(q, tickers, market=market)
    return {"ticker": ticker}


@app.get("/api/symbols-missing")
def api_symbols_missing(
    limit: int = Query(50, ge=0, le=5000),
    period: str = Query("All periods"),
    market: str = Query("india"),
):
    """Symbols missing Sharia data, optionally for a specific period.

    Returns:
      - never_screened: symbols with zero data in cache
      - missing_for_period: symbols screened but lacking data for selected period
      - symbols: combined list (never_screened first) for compute
    """
    from modules.sharia.data import format_date_ordinal

    tickers, _ = get_universe(market=market)
    cached = get_cached_sharia(market=market)

    if cached is None or cached.empty:
        return {
            "symbols": tickers[:limit] if limit else tickers,
            "total_missing": len(tickers),
            "never_screened": len(tickers),
            "missing_for_period": 0,
        }

    have_any = set(cached["symbol"].unique())
    never_screened = [t for t in tickers if t not in have_any]

    missing_for_period_list: list[str] = []
    if period and period != "All periods":
        # Symbols that have SOME data but not for the selected period
        period_df = cached.dropna(subset=["report_period"]).copy()
        period_df["_fmt"] = period_df["report_period"].map(format_date_ordinal)
        have_period = set(period_df[period_df["_fmt"] == period]["symbol"].unique())
        missing_for_period_list = [t for t in tickers if t in have_any and t not in have_period]

    combined = never_screened + missing_for_period_list
    return {
        "symbols": combined[:limit] if limit else combined,
        "total_missing": len(combined),
        "never_screened": len(never_screened),
        "missing_for_period": len(missing_for_period_list),
    }


class ComputeBody(BaseModel):
    symbols: list[str]
    max_workers: int = 5
    force: bool = False  # True = re-fetch all, False = smart (skip up-to-date symbols)
    market: str = "india"


def _symbols_needing_refresh(symbols: list[str], cached: pd.DataFrame | None) -> list[str]:
    """Return symbols that are missing the latest expected quarter in cache."""
    from modules.sharia.filter import _last_quarter_end, ANNUAL_END
    from datetime import date

    if cached is None or cached.empty:
        return symbols

    latest_expected = _last_quarter_end(date.today())
    # If latest expected quarter is within the annual range, use annual end
    if latest_expected <= ANNUAL_END:
        latest_expected = ANNUAL_END

    cached_symbols = set(cached["symbol"].unique())
    need_refresh = []
    for sym in symbols:
        resolved = _resolve_symbol_for_cache(sym, cached_symbols)
        if resolved not in cached_symbols:
            need_refresh.append(sym)
            continue
        sym_df = cached[cached["symbol"] == resolved]
        periods = pd.to_datetime(sym_df["report_period"], errors="coerce").dropna()
        if periods.empty:
            need_refresh.append(sym)
            continue
        latest_cached = periods.max().date()
        if latest_cached < latest_expected:
            need_refresh.append(sym)
    return need_refresh


def _resolve_symbols_for_compute(symbols: list[str], market: str = "india") -> list[str]:
    """Resolve base names to Yahoo Finance tickers.
    India: TCS → TCS.NS, INFY → INFY.NS
    US: AAPL → AAPL (bare, no suffix)
    """
    tickers, _ = get_universe(market=market)
    ticker_set = set(tickers)
    resolved = []
    for s in symbols:
        s = s.strip().upper()
        if "." in s:
            resolved.append(s)
        elif market == "us":
            # US symbols are bare — accept as-is if in universe or unknown
            resolved.append(s)
        else:
            # India: look up .NS or .BO suffix
            for suffix in (".NS", ".BO"):
                if s + suffix in ticker_set:
                    resolved.append(s + suffix)
                    break
            else:
                resolved.append(s + ".NS")
    return list(dict.fromkeys(resolved))  # deduplicate, preserve order


@app.post("/api/compute-sharia")
def api_compute_sharia(body: ComputeBody):
    """Compute Sharia metrics for given symbols and save to cache.

    force=True: re-fetch all symbols from Yahoo Finance.
    force=False (default): only fetch symbols missing the latest expected period.
    """
    if not body.symbols:
        raise HTTPException(400, "symbols must be non-empty")

    market = body.market
    # Resolve base names to full tickers before any processing
    all_resolved = _resolve_symbols_for_compute(body.symbols, market=market)
    cached = get_cached_sharia(market=market)

    if body.force:
        to_fetch = all_resolved
    else:
        to_fetch = _symbols_needing_refresh(all_resolved, cached)

    if not to_fetch:
        return {"computed": 0, "skipped": len(all_resolved), "message": "All symbols up to date"}

    results = compute_sharia_metrics(to_fetch, max_workers=body.max_workers, market=market)
    new_df = pd.DataFrame(results)
    if cached is not None and len(cached) > 0:
        existing = cached[~cached["symbol"].isin(to_fetch)]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    try:
        save_sharia_cache(combined, market=market)
        mark_refreshed("sharia", to_fetch, source="yfinance")
    except Exception as e:
        raise HTTPException(500, str(e))
    skipped = len(body.symbols) - len(to_fetch)
    return {"computed": len(to_fetch), "skipped": skipped, "period_rows": len(results)}


@app.get("/api/portfolio-options")
def api_portfolio_options(market: str = Query("india")):
    """Name labels for all cached symbols, for the symbol picker dropdown."""
    tickers, _ = get_universe(market=market)
    cached = get_cached_sharia(market=market)
    labels: dict[str, str] = {}
    if cached is not None and not cached.empty:
        # Use the latest entry per symbol to build name labels.
        df = cached.copy()
        if "report_period" in df.columns:
            df["_dt"] = pd.to_datetime(df["report_period"], errors="coerce")
            df = df.sort_values(["symbol", "_dt"]).groupby("symbol", as_index=False).last()
        else:
            df = df.groupby("symbol", as_index=False).last()
        for _, row in df.iterrows():
            sym = row["symbol"]
            name = row.get("name") or sym
            sharia_val = row.get("Sharia", row.get("compliant"))
            comp = (
                "Compliant" if sharia_val == ShariaStatus.YES.value
                else "Not compliant" if sharia_val == ShariaStatus.NO.value
                else ""
            )
            labels[sym] = f"{sym} — {name}" + (f" ({comp})" if comp else "")
    # Symbols are already available via /api/universe — return only labels here.
    return {"symbols": [], "labels": labels}


class PortfolioDataBody(BaseModel):
    symbols: list[str]
    period: str = "31st March 2025"
    market: str = "india"


def _resolve_symbol_for_cache(symbol: str, in_cache: set) -> str:
    """Resolve base name (TCS) to cache ticker (TCS.NS) if present."""
    s = (symbol or "").strip().upper()
    if s in in_cache:
        return s
    if "." not in s:
        for suffix in (".NS", ".BO"):
            if (s + suffix) in in_cache:
                return s + suffix
    return s


@app.post("/api/portfolio-data")
def api_portfolio_data(body: PortfolioDataBody):
    """Portfolio table and pivot (Sharia status by year/quarter)."""
    cached = get_cached_sharia(market=body.market)
    _, exchange_map = get_universe(market=body.market)
    if cached is None:
        return {"pivot": {}, "rows": [], "missing": body.symbols}
    df_full = cached.copy()
    df_full["exchange"] = df_full["symbol"].map(exchange_map)
    in_cache = set(df_full["symbol"].unique())
    resolved = [_resolve_symbol_for_cache(s, in_cache) for s in body.symbols]
    portfolio_in = [r for r in resolved if r in in_cache]
    missing = [body.symbols[i] for i in range(len(body.symbols)) if resolved[i] not in in_cache]
    if not portfolio_in:
        return {"pivot": {}, "rows": [], "missing": body.symbols}

    pf_df = df_full[df_full["symbol"].isin(portfolio_in)].copy()
    pf_df["report_period_dt"] = pd.to_datetime(pf_df["report_period"], errors="coerce")
    pf_mat = pf_df.dropna(subset=["report_period_dt"]).copy()
    if "industry_compliant" not in pf_mat.columns:
        pf_mat["industry_compliant"] = pf_mat.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    pf_mat["Sharia"] = pf_mat.apply(
        lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
    )
    mar2025 = pd.Timestamp("2025-03-31")

    def period_label(row):
        d = row["report_period_dt"]
        if d <= mar2025:
            return d.year
        q = {3: 1, 6: 2, 9: 3, 12: 4}.get(d.month, (d.month + 2) // 3)
        return f"{d.year}-Q{q}"

    pf_mat["period_label"] = pf_mat.apply(period_label, axis=1)
    period_status = (
        pf_mat.sort_values("report_period_dt")
        .groupby(["symbol", "period_label"], as_index=False)["Sharia"]
        .last()
    )
    pivot_df = period_status.pivot(index="symbol", columns="period_label", values="Sharia")
    pivot_df = pivot_df.sort_index()
    # Ensure all column names are strings so JSON key order is preserved
    pivot_df.columns = [str(c) for c in pivot_df.columns]
    pivot_reset = pivot_df.reset_index()
    other_cols = sorted([c for c in pivot_reset.columns if c != "symbol"])
    pivot_reset = pivot_reset[["symbol"] + other_cols]
    pivot_list = _df_to_records(pivot_reset)

    if body.period != "All periods":
        pf_df = pf_df[pf_df["report_period"].map(format_date_ordinal) == body.period]
    pf_df["report_period"] = pf_df["report_period"].map(
        lambda x: format_date_ordinal(x) if pd.notna(x) and x else ""
    )
    if "industry_compliant" not in pf_df.columns:
        pf_df["industry_compliant"] = pf_df.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    pf_df["Sharia"] = pf_df.apply(
        lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
    )
    cols = [c for c in SHARIA_TABLE_COLUMNS if c in pf_df.columns]
    rows = _df_to_records(pf_df[cols])

    return {"pivot": pivot_list, "pivot_columns": list(pivot_df.columns) if not pivot_df.empty else [], "rows": rows, "missing": missing}


class ReplacementBody(BaseModel):
    symbol: str
    sector: str | None = None
    industry: str | None = None
    exclude_symbols: list[str] = []
    market: str = "india"
    top_n: int = 5


@app.post("/api/portfolio/replacements")
def api_portfolio_replacements(body: ReplacementBody):
    """Return top Sharia-compliant replacements for a non-compliant symbol, same sector."""
    cached = get_cached_sharia(market=body.market)
    if cached is None:
        return {"replacements": []}
    df = cached.copy()
    # Enrich
    if "industry_compliant" not in df.columns:
        df["industry_compliant"] = df.apply(
            lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
        )
    df["Sharia"] = df.apply(lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1)
    # Latest period per symbol
    df = df.sort_values("report_period").groupby("symbol", as_index=False).last()
    # Filter: compliant, not the offending symbol, not in exclude list
    exclude = set([body.symbol] + (body.exclude_symbols or []))
    df = df[(df["Sharia"] == "Yes") & (~df["symbol"].isin(exclude))]
    # Prefer same sector
    sector_match = df[df["sector"] == body.sector] if body.sector else df
    if len(sector_match) < 3:
        sector_match = df  # widen if sector too narrow
    # Sort by market cap desc, take top N
    sector_match = sector_match.copy()
    sector_match["market_cap"] = pd.to_numeric(sector_match["market_cap"], errors="coerce").fillna(0)
    top = sector_match.sort_values("market_cap", ascending=False).head(body.top_n)
    cols = ["symbol", "name", "sector", "industry", "market_cap", "debt_to_equity_ratio",
            "cash_to_assets_pct", "receivables_to_assets_pct", "Sharia"]
    cols = [c for c in cols if c in top.columns]
    return {"replacements": _df_to_records(top[cols])}


@app.get("/api/compare")
def api_compare(symbols: str = Query(""), market: str = Query("india")):
    """Compare multiple symbols with Sharia + live market metrics."""
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return {"rows": []}
    cached = get_cached_sharia(market=market)
    _, exchange_map = get_universe(market=market)

    # Build base rows from Sharia cache
    sharia_rows: dict = {}
    if cached is not None and not cached.empty:
        df = cached[cached["symbol"].isin(sym_list)].copy()
        if not df.empty:
            df = df.sort_values(["symbol", "report_period"]).groupby("symbol").last().reset_index()
            if "industry_compliant" not in df.columns:
                df["industry_compliant"] = df.apply(
                    lambda r: is_industry_compliant(r.get("industry"), r.get("sector")), axis=1
                )
            df["Sharia"] = df.apply(
                lambda r: effective_sharia(r["compliant"], r.get("industry_compliant")), axis=1
            )
            for _, row in df.iterrows():
                sharia_rows[row["symbol"]] = {
                    "symbol": row["symbol"],
                    "name": row.get("name") or row["symbol"],
                    "Sharia": row.get("Sharia"),
                    "industry": row.get("industry"),
                    "sector": row.get("sector"),
                    "market_cap": _safe_val(row.get("market_cap")),
                    "debt_to_equity_ratio": _safe_val(row.get("debt_to_equity_ratio")),
                    "cash_to_assets_pct": _safe_val(row.get("cash_to_assets_pct")),
                    "other_revenue_to_revenue_pct": _safe_val(row.get("other_revenue_to_revenue_pct")),
                    "receivables_to_assets_pct": _safe_val(row.get("receivables_to_assets_pct")),
                }

    # Enrich with live yfinance market + valuation data
    rows = []
    for sym in sym_list:
        base = sharia_rows.get(sym, {"symbol": sym, "name": sym, "Sharia": None})
        try:
            mkt = yf_get_section(sym, "market", force=False, market=market)
            val = yf_get_section(sym, "valuation", force=False, market=market)
            fin = yf_get_section(sym, "financials", force=False, market=market)
            ov  = yf_get_section(sym, "overview", force=False, market=market)
            base["current_price"] = _safe_val(mkt.get("currentPrice") or val.get("currentPrice"))
            base["52w_high"] = _safe_val(mkt.get("fiftyTwoWeekHigh"))
            base["52w_low"] = _safe_val(mkt.get("fiftyTwoWeekLow"))
            base["52w_change_pct"] = _safe_val(mkt.get("fiftyTwoWeekChangePercent") or mkt.get("52WeekChange"))
            base["beta"] = _safe_val(mkt.get("beta"))
            base["dividend_yield"] = _safe_val(mkt.get("dividendYield") or val.get("dividendYield"))
            base["trailing_pe"] = _safe_val(val.get("trailingPE") or mkt.get("trailingPE"))
            base["forward_pe"] = _safe_val(val.get("forwardPE") or mkt.get("forwardPE"))
            base["price_to_book"] = _safe_val(val.get("priceToBook") or mkt.get("priceToBook"))
            base["ev_to_ebitda"] = _safe_val(val.get("enterpriseToEbitda") or val.get("evToEbitda"))
            base["roe"] = _safe_val(fin.get("returnOnEquity") or ov.get("returnOnEquity"))
            base["roa"] = _safe_val(fin.get("returnOnAssets") or ov.get("returnOnAssets"))
            base["profit_margin"] = _safe_val(fin.get("profitMargins") or ov.get("profitMargins"))
            base["revenue_growth"] = _safe_val(fin.get("revenueGrowth") or ov.get("revenueGrowth"))
            base["earnings_growth"] = _safe_val(fin.get("earningsGrowth") or ov.get("earningsGrowth"))
            base["debt_to_equity_live"] = _safe_val(fin.get("debtToEquity") or ov.get("debtToEquity"))
            base["current_ratio"] = _safe_val(fin.get("currentRatio") or ov.get("currentRatio"))
            base["employees"] = _safe_val(ov.get("fullTimeEmployees"))
            if not base.get("name") or base["name"] == sym:
                base["name"] = ov.get("shortName") or ov.get("longName") or mkt.get("shortName") or sym
            if not base.get("market_cap"):
                base["market_cap"] = _safe_val(val.get("marketCap") or mkt.get("marketCap"))
        except Exception:
            pass
        rows.append(base)

    return {"rows": rows}


def _safe_val(v):
    """Convert numpy/nan values to Python native or None."""
    if v is None:
        return None
    try:
        if hasattr(v, "item"):
            v = v.item()
        if isinstance(v, float) and (v != v):  # NaN check
            return None
        return v
    except Exception:
        return None


# ----- Watchlist -----

class WatchlistAddBody(BaseModel):
    symbol: str


@app.get("/api/watchlist")
def api_get_watchlist():
    """Return current watchlist symbols with Sharia status enrichment."""
    symbols = _load_watchlist()
    cached = get_cached_sharia()
    rows = []
    for sym in symbols:
        row: dict = {"symbol": sym}
        if cached is not None and not cached.empty:
            match = cached[cached["symbol"] == sym]
            if not match.empty:
                latest = match.sort_values("report_period").iloc[-1]
                row["name"] = latest.get("name") or sym
                row["Sharia"] = latest.get("Sharia") or "Unknown"
                row["industry"] = latest.get("industry")
                row["sector"] = latest.get("sector")
                row["report_period"] = format_date_ordinal(latest.get("report_period"))
        rows.append(row)
    return {"symbols": symbols, "rows": rows, "count": len(symbols)}


@app.post("/api/watchlist")
def api_add_watchlist(body: WatchlistAddBody):
    """Add a symbol to the watchlist."""
    sym = (body.symbol or "").strip().upper()
    if not sym:
        raise HTTPException(400, "symbol is required")
    symbols = _load_watchlist()
    if sym not in symbols:
        symbols.append(sym)
        _save_watchlist(symbols)
    return {"ok": True, "symbols": _load_watchlist(), "count": len(_load_watchlist())}


@app.delete("/api/watchlist/{symbol}")
def api_remove_watchlist(symbol: str):
    """Remove a symbol from the watchlist."""
    sym = (symbol or "").strip().upper()
    symbols = _load_watchlist()
    symbols = [s for s in symbols if s != sym]
    _save_watchlist(symbols)
    return {"ok": True, "symbols": symbols, "count": len(symbols)}


# ----- Benchmarks -----

@app.get("/api/benchmarks")
def api_list_benchmarks():
    """List all locally configured benchmark definitions."""
    return {"benchmarks": list_benchmarks()}


@app.get("/api/benchmarks/{benchmark_id}")
def api_get_benchmark(benchmark_id: str):
    """Return a specific benchmark definition."""
    try:
        data = load_benchmark(benchmark_id)
        return data
    except ValueError as e:
        raise HTTPException(404, str(e))


# ----- Quality Screener -----

class QualityComputeBody(BaseModel):
    symbols: list[str] = []
    workers: int = 5
    force: bool = False
    market: str = "india"


@app.get("/api/symbol/{symbol}/quality")
def api_symbol_quality(symbol: str, force: bool = False, market: str = Query("india")):
    """Compute (or return cached) quality score for one symbol."""
    # Pass latest Sharia row for better D/E scoring
    cached = get_cached_sharia(market=market)
    sharia_row = None
    if cached is not None and not cached.empty:
        match = cached[cached["symbol"] == symbol]
        if not match.empty:
            sharia_row = match.sort_values("report_period").iloc[-1].to_dict()
    try:
        result = compute_quality_score(symbol, force=force, sharia_row=sharia_row, market=market)
        return _sanitize(result)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/quality/compute")
def api_quality_compute(body: QualityComputeBody):
    """Batch compute quality scores. If symbols is empty, uses all Sharia-compliant stocks."""
    cached = get_cached_sharia(market=body.market)
    sharia_rows: dict = {}

    if body.symbols:
        symbols = [s.strip().upper() for s in body.symbols if s.strip()]
    else:
        # Default: all Sharia-compliant symbols in cache
        if cached is not None and not cached.empty:
            df = cached.copy()
            df["_dt"] = pd.to_datetime(df["report_period"], errors="coerce")
            df = df.sort_values(["symbol", "_dt"]).groupby("symbol", as_index=False).last()
            df = df[df["Sharia"] == "Yes"]
            symbols = df["symbol"].tolist()
        else:
            symbols = []

    # Build sharia_rows lookup for D/E enrichment
    if cached is not None and not cached.empty:
        df2 = cached.copy()
        df2["_dt"] = pd.to_datetime(df2["report_period"], errors="coerce")
        df2 = df2.sort_values(["symbol", "_dt"]).groupby("symbol", as_index=False).last()
        sharia_rows = {row["symbol"]: row for row in df2.to_dict("records")}

    if not symbols:
        return {"computed": 0, "symbols": [], "message": "No symbols to compute."}

    results = batch_compute_quality(
        symbols=symbols,
        workers=min(body.workers, 10),
        force=body.force,
        sharia_rows=sharia_rows,
        market=body.market,
    )
    errors = [r["symbol"] for r in results if r.get("error")]
    return _sanitize({
        "computed": len(results),
        "errors": errors,
        "error_count": len(errors),
        "symbols": [r["symbol"] for r in results],
    })


@app.get("/api/screener")
def api_screener(
    min_score: int = Query(0, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    sector: str = Query(""),
    sharia_only: bool = Query(True),
    sort_by: str = Query("total_score"),
    limit: int = Query(0, ge=0),
    market: str = Query("india"),
):
    """
    Return quality-scored stocks, joined with Sharia data.
    Only returns symbols where quality has been computed.
    """
    quality_cache = load_quality_cache()
    if not quality_cache:
        return {"rows": [], "total": 0, "computed_count": 0, "missing_count": 0,
                "message": "No quality scores computed yet. Run POST /api/quality/compute first."}

    cached = get_cached_sharia(market=market)
    sharia_lookup: dict = {}
    if cached is not None and not cached.empty:
        df = cached.copy()
        df["_dt"] = pd.to_datetime(df["report_period"], errors="coerce")
        df = df.sort_values(["symbol", "_dt"]).groupby("symbol", as_index=False).last()
        sharia_lookup = {row["symbol"]: row for row in df.to_dict("records")}

    tickers, _ = get_universe(market=market)
    total_universe = len(tickers)

    rows = []
    for symbol, qscore in quality_cache.items():
        if qscore.get("total_score") is None:
            continue

        total = qscore["total_score"]
        if total < min_score or total > max_score:
            continue

        sharia_row = sharia_lookup.get(symbol, {})
        sharia_status = sharia_row.get("Sharia", "Unknown")

        if sharia_only and sharia_status != "Yes":
            continue

        stock_sector = sharia_row.get("sector") or ""
        if sector and sector.lower() not in stock_sector.lower():
            continue

        row = {
            "symbol": symbol,
            "name": sharia_row.get("name") or symbol,
            "Sharia": sharia_status,
            "sector": stock_sector,
            "industry": sharia_row.get("industry"),
            "market_cap": sharia_row.get("market_cap"),
            "total_score": total,
            "label": qscore.get("label"),
            "data_quality": qscore.get("data_quality"),
            "profitability_score": qscore.get("profitability_score"),
            "cash_generation_score": qscore.get("cash_generation_score"),
            "financial_strength_score": qscore.get("financial_strength_score"),
            "valuation_score": qscore.get("valuation_score"),
            # Profitability
            "roe": qscore.get("roe"),
            "roa": qscore.get("roa"),
            "operating_margin": qscore.get("operating_margin"),
            "gross_margin": qscore.get("gross_margin"),
            "net_margin": qscore.get("net_margin"),
            "ebitda_margin": qscore.get("ebitda_margin"),
            "roce": qscore.get("roce"),
            # Growth
            "revenue_growth": qscore.get("revenue_growth"),
            "earnings_growth": qscore.get("earnings_growth"),
            # Financial health
            "fcf_conversion": qscore.get("fcf_conversion"),
            "debt_to_equity": qscore.get("debt_to_equity"),
            "current_ratio": qscore.get("current_ratio"),
            "quick_ratio": qscore.get("quick_ratio"),
            "interest_coverage": qscore.get("interest_coverage"),
            # Valuation
            "peg_ratio": qscore.get("peg_ratio"),
            "trailing_pe": qscore.get("trailing_pe"),
            "forward_pe": qscore.get("forward_pe"),
            "price_to_book": qscore.get("price_to_book"),
            "ev_to_ebitda": qscore.get("ev_to_ebitda"),
            "price_to_sales": qscore.get("price_to_sales"),
            "ev_to_revenue": qscore.get("ev_to_revenue"),
            # Market
            "beta": qscore.get("beta"),
            "dividend_yield": qscore.get("dividend_yield"),
            "payout_ratio": qscore.get("payout_ratio"),
            "vs_200dma": qscore.get("vs_200dma"),
            "computed_at": qscore.get("computed_at"),
        }
        rows.append(row)

    # Sort
    valid_sorts = {"total_score", "profitability_score", "cash_generation_score",
                   "financial_strength_score", "valuation_score", "roe", "peg_ratio"}
    sort_key = sort_by if sort_by in valid_sorts else "total_score"
    rows.sort(key=lambda r: (r.get(sort_key) or 0), reverse=True)

    if limit and limit > 0:
        rows = rows[:limit]

    return _sanitize({
        "rows": rows,
        "total": len(rows),
        "computed_count": len(quality_cache),
        "missing_count": max(0, total_universe - len(quality_cache)),
    })


# ----- Cache clear -----

class CacheClearBody(BaseModel):
    module: str = "all"
    market: str = "india"


@app.post("/api/cache/clear")
def api_cache_clear(body: CacheClearBody):
    """Clear cached data for a module (default: all)."""
    from modules.sharia import get_sharia_cache_path
    module = (body.module or "all").lower()
    cleared = []
    if module in ("sharia", "all"):
        cache_file = get_sharia_cache_path(body.market)
        if cache_file.exists():
            cache_file.unlink()
            cleared.append(f"sharia_{body.market}")
    return {"ok": True, "cleared": cleared, "module": module}


@app.get("/api/cache-status")
def api_cache_status(market: str = Query("india")):
    """Cache freshness information for the frontend staleness banner."""
    tickers, _ = get_universe(market=market)
    cached = get_cached_sharia(market=market)
    sharia_staleness = get_staleness("sharia", max_age_hours=72)

    symbols_with_data = 0
    if cached is not None:
        symbols_with_data = cached["symbol"].nunique()

    return {
        "sharia": {
            **sharia_staleness,
            "symbols_with_data": symbols_with_data,
            "symbols_missing": len(tickers) - symbols_with_data,
            "total_universe": len(tickers),
        },
        "refresh_commands": {
            "cli": "./cli.py compute sharia --missing",
            "skill": "Use the investment skill to refresh data",
        },
    }
