#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investment Platform CLI — single entry point for all operations.

Usage: ./cli.py <command> [options]
       python cli.py <command> [options]

Exit codes:
  0 — success
  1 — error (bad args, network failure)
  2 — partial success, some data needs web fetch (JSON includes needs_web_fetch)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def cmd_universe(args):
    """List tickers or show universe stats."""
    from modules.universe import load_universe
    from core.output import print_output

    tickers, exchange_map = load_universe(market=args.market)

    if args.stats:
        nse = sum(1 for v in exchange_map.values() if v == "NSE")
        bse = sum(1 for v in exchange_map.values() if v == "BSE")
        print_output({
            "market": args.market,
            "total": len(tickers),
            "nse": nse,
            "bse": bse,
        }, fmt=args.format)
        return 0

    if args.exchange:
        ex = args.exchange.upper()
        tickers = [t for t in tickers if exchange_map.get(t, "").upper() == ex]

    records = [{"symbol": t, "exchange": exchange_map.get(t, "")} for t in tickers]
    if args.limit:
        records = records[:args.limit]
    print_output(records, fmt=args.format)
    return 0


def cmd_sharia(args):
    """Show Sharia status for a symbol or list compliant stocks."""
    from modules.sharia import (
        load_cached_sharia, enrich_cached_sharia, format_date_ordinal,
        get_report_period_options, ShariaStatus,
    )
    from core.output import print_output, print_error

    cached = load_cached_sharia()
    if cached is None:
        print_error("No Sharia data cached. Run: ./cli.py compute sharia", fmt=args.format)
        return 1

    cached = enrich_cached_sharia(cached)

    # Parse positional args: "list" or a symbol name
    positionals = args.args
    subaction = None
    symbol = None
    if positionals:
        if positionals[0].lower() == "list":
            subaction = "list"
        else:
            symbol = positionals[0]

    if subaction == "list":
        # List all compliant stocks
        period = args.period or "All periods"
        df = cached.copy()
        if period != "All periods":
            df = df[df["report_period"].map(format_date_ordinal) == period]
        df = df[df["Sharia"] == ShariaStatus.YES.value]
        df = df.sort_values("symbol").drop_duplicates(subset=["symbol"], keep="last")
        keys = ["symbol", "name", "Sharia", "industry", "sector"]
        print_output(df[keys].to_dict("records"), fmt=args.format)
        return 0

    # Single symbol lookup
    if not symbol:
        print_error("Symbol required. Usage: ./cli.py sharia TCS.NS", fmt=args.format)
        return 1

    # Resolve base name
    market = getattr(args, "market", "india")
    if "." not in symbol:
        from modules.universe import load_universe
        tickers, _ = load_universe(market=market)
        from modules.sharia import resolve_search_to_ticker
        resolved = resolve_search_to_ticker(symbol, tickers, market=market)
        if resolved:
            symbol = resolved

    df = cached[cached["symbol"] == symbol]
    if df.empty:
        print_error(f"Symbol {symbol} not in cache. Run: ./cli.py compute sharia --symbols {symbol}", fmt=args.format)
        return 1

    if args.periods:
        records = df.sort_values("report_period").to_dict("records")
        for r in records:
            r["report_period"] = format_date_ordinal(r.get("report_period"))
    else:
        row = df.sort_values("report_period").iloc[-1].to_dict()
        row["report_period"] = format_date_ordinal(row.get("report_period"))
        records = [row]

    keys = ["symbol", "name", "report_period", "Sharia", "debt_to_equity_ratio",
            "cash_to_assets_pct", "other_revenue_to_revenue_pct", "receivables_to_assets_pct",
            "industry", "sector", "market_cap"]
    print_output(records, fmt=args.format, keys=keys)
    return 0


def cmd_compute(args):
    """Compute Sharia metrics and save to cache."""
    from modules.sharia import (
        compute_sharia_metrics, load_cached_sharia, save_sharia_cache,
        DEFAULT_PORTFOLIO, parse_portfolio_symbols,
    )
    from modules.universe import load_universe
    from core.cache import mark_refreshed
    from core.output import print_output, print_error
    import pandas as pd

    if args.module != "sharia":
        print_error(f"Unknown compute module: {args.module}. Supported: sharia", fmt=args.format)
        return 1

    market = getattr(args, "market", "india")
    tickers, _ = load_universe(market=market)
    cached = load_cached_sharia(market=market)
    cached_symbols = set(cached["symbol"].unique().tolist()) if cached is not None and len(cached) > 0 else set()

    if args.portfolio:
        from modules.sharia import DEFAULT_PORTFOLIO_MAP
        args.symbols = DEFAULT_PORTFOLIO_MAP.get(market, DEFAULT_PORTFOLIO).strip()

    if args.symbols:
        bases = [s.strip().upper() for s in args.symbols.replace(",", "\n").split() if s.strip()]
        to_fetch = []
        for s in bases:
            if "." in s:
                to_fetch.append(s)
            elif market == "us":
                to_fetch.append(s)
            else:
                for suffix in (".NS", ".BO"):
                    if s + suffix in tickers:
                        to_fetch.append(s + suffix)
                        break
                else:
                    to_fetch.append(s + ".NS")
        to_fetch = list(dict.fromkeys(to_fetch))
    elif args.missing:
        missing = [t for t in tickers if t not in cached_symbols]
        n = args.limit or len(missing)
        to_fetch = missing[:n]
    else:
        print_error("Specify --symbols, --portfolio, or --missing", fmt=args.format)
        return 1

    if not to_fetch:
        print_output({"message": "Nothing to compute. Cache is up to date."}, fmt=args.format)
        return 0

    # Smart mode: skip symbols already up to date unless --force
    if not args.force and cached is not None and len(cached) > 0:
        from modules.sharia.filter import _last_quarter_end, ANNUAL_END
        from datetime import date
        latest_expected = _last_quarter_end(date.today())
        if latest_expected <= ANNUAL_END:
            latest_expected = ANNUAL_END
        need_refresh = []
        for sym in to_fetch:
            sym_df = cached[cached["symbol"] == sym]
            if sym_df.empty:
                need_refresh.append(sym)
                continue
            periods = pd.to_datetime(sym_df["report_period"], errors="coerce").dropna()
            if periods.empty or periods.max().date() < latest_expected:
                need_refresh.append(sym)
        skipped = len(to_fetch) - len(need_refresh)
        if skipped and not args.quiet:
            print(f"Smart mode: {skipped} symbol(s) already up to date, skipping. Use --force to re-fetch all.", file=sys.stderr)
        to_fetch = need_refresh

    if not to_fetch:
        print_output({"message": "All symbols up to date.", "skipped": len(to_fetch)}, fmt=args.format)
        return 0

    if not args.quiet:
        print(f"Computing {len(to_fetch)} symbol(s), workers={args.workers}...", file=sys.stderr)

    results = compute_sharia_metrics(to_fetch, max_workers=args.workers, market=market)
    new_df = pd.DataFrame(results)

    if cached is not None and len(cached) > 0:
        existing = cached[~cached["symbol"].isin(to_fetch)]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    save_sharia_cache(combined, market=market)
    mark_refreshed("sharia", to_fetch, source="yfinance")

    compliant_count = sum(1 for r in results if r.get("Sharia") == "Yes")
    summary = {
        "computed": len(to_fetch),
        "period_rows": len(results),
        "compliant": compliant_count,
    }

    if not args.quiet:
        print(f"Done. {len(to_fetch)} symbols -> {len(results)} rows ({compliant_count} compliant)", file=sys.stderr)

    print_output(summary, fmt=args.format)
    return 0


def cmd_lookup(args):
    """Fetch detailed yfinance data for a symbol."""
    from modules.market import get_section_data
    from core.output import print_output, print_error

    symbol = args.symbol
    section = args.section

    if not symbol:
        print_error("Symbol required. Usage: ./cli.py lookup TCS.NS --section financials", fmt=args.format)
        return 1

    data = get_section_data(symbol, section, force=args.force)
    if "error" in data:
        print_error(data["error"], fmt=args.format)
        return 1

    print_output(data, fmt=args.format)
    return 0


def cmd_compare(args):
    """Compare multiple symbols side by side."""
    from modules.sharia import load_cached_sharia, enrich_cached_sharia, format_date_ordinal
    from core.output import print_output, print_error

    symbols = [s.strip() for s in args.symbols if s.strip()]
    if not symbols:
        print_error("At least 2 symbols required.", fmt=args.format)
        return 1

    cached = load_cached_sharia()
    if cached is None:
        print_error("No Sharia data cached.", fmt=args.format)
        return 1

    cached = enrich_cached_sharia(cached)

    # Resolve base names
    from modules.universe import load_universe
    tickers, exchange_map = load_universe(market="india")
    from modules.sharia import resolve_search_to_ticker
    resolved = []
    for s in symbols:
        r = resolve_search_to_ticker(s, tickers)
        resolved.append(r or s)

    df = cached[cached["symbol"].isin(resolved)].copy()
    if df.empty:
        print_error(f"None of {resolved} found in cache.", fmt=args.format)
        return 1

    df = df.sort_values(["symbol", "report_period"]).groupby("symbol").last().reset_index()
    df["exchange"] = df["symbol"].map(exchange_map)
    keys = ["symbol", "name", "Sharia", "industry", "sector", "market_cap",
            "debt_to_equity_ratio", "cash_to_assets_pct", "other_revenue_to_revenue_pct",
            "receivables_to_assets_pct"]
    print_output(df[keys].to_dict("records"), fmt=args.format)
    return 0


def cmd_portfolio_index(args):
    """Analyze a personal portfolio against a Sharia-filtered benchmark."""
    from modules.portfolio import analyze_personal_index, parse_holdings_arg
    from core.output import print_output, print_error

    holdings = parse_holdings_arg(args.holdings)
    if not holdings:
        print_error(
            "Provide holdings like TCS:10,INFY:8 or MARUTI.NS:2:11850",
            fmt=args.format,
        )
        return 1

    try:
        result = analyze_personal_index(
            holdings=holdings,
            benchmark_id=args.benchmark,
            sip_amount=args.sip,
            strict_no_sell=not args.allow_sells,
            max_buy_suggestions=args.max_buy_suggestions,
        )
    except ValueError as e:
        print_error(str(e), fmt=args.format)
        return 1

    if result.get("error"):
        print_error(result["error"], fmt=args.format)
        return 1

    print_output(result, fmt=args.format)
    return 0


def cmd_portfolio(args):
    """Policy-aware portfolio analysis and position sizing."""
    from core.output import print_error

    action = getattr(args, "port_action", None)
    if action == "analyze":
        return cmd_portfolio_analyze(args)
    if action == "size":
        return cmd_portfolio_size(args)
    print_error("Specify a subcommand: analyze or size", fmt=args.format)
    return 1


def cmd_portfolio_analyze(args):
    """Gap analysis against personal portfolio policy."""
    from modules.portfolio import parse_holdings_arg
    from modules.portfolio.policy import analyze_portfolio
    from core.output import print_output, print_error

    holdings = parse_holdings_arg(args.holdings)
    if not holdings:
        print_error("Provide holdings like TCS.NS:9,INFY.NS:24", fmt=args.format)
        return 1

    result = analyze_portfolio(holdings)
    if result.get("error"):
        print_error(result["error"], fmt=args.format)
        return 1

    print_output(result, fmt=args.format)
    return 0


def cmd_portfolio_size(args):
    """Position sizing: how many units to buy respecting policy limits."""
    from modules.portfolio import parse_holdings_arg
    from modules.portfolio.sizer import compute_position_size
    from core.output import print_output, print_error

    holdings = parse_holdings_arg(args.holdings)
    if not holdings:
        print_error("Provide holdings like TCS.NS:9,INFY.NS:24", fmt=args.format)
        return 1

    result = compute_position_size(
        symbol=args.symbol,
        holdings=holdings,
        sip_amount=args.sip,
    )
    if result.get("error"):
        print_error(result["error"], fmt=args.format)
        return 1

    print_output(result, fmt=args.format)
    return 0


def cmd_universe_suggest(args):
    """Sharia-compliant candidates for a sector + cap tier slot."""
    from modules.universe.suggest import suggest_candidates
    from core.output import print_output, print_error

    exclude = [s.strip() for s in args.exclude.split(",")] if args.exclude else []

    result = suggest_candidates(
        sector_keyword=args.sector,
        cap_tier=args.cap,
        exclude_symbols=exclude,
        force_sharia=args.force_sharia,
        max_results=args.max,
    )
    if result.get("error"):
        print_error(result["error"], fmt=args.format)
        return 1

    print_output(result, fmt=args.format)
    return 0


def cmd_watchlist(args):
    """Manage the watchlist of stocks to track."""
    import json
    from pathlib import Path
    from core.config import DB_DIR
    from core.output import print_output, print_error

    WATCHLIST_PATH = DB_DIR / "watchlist.json"

    def _load() -> list[str]:
        if not WATCHLIST_PATH.exists():
            return []
        try:
            data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
            return [str(s) for s in data.get("symbols", []) if s]
        except (json.JSONDecodeError, OSError):
            return []

    def _save(symbols: list[str]) -> None:
        seen: set[str] = set()
        unique = []
        for s in symbols:
            s = s.strip().upper()
            if s and s not in seen:
                seen.add(s)
                unique.append(s)
        DB_DIR.mkdir(parents=True, exist_ok=True)
        WATCHLIST_PATH.write_text(json.dumps({"symbols": unique}, indent=2), encoding="utf-8")

    action = args.action

    if action == "list":
        symbols = _load()
        if not symbols:
            print_output({"symbols": [], "count": 0, "message": "Watchlist is empty."}, fmt=args.format)
            return 0
        # Enrich with Sharia status if available
        try:
            from modules.sharia import load_cached_sharia, enrich_cached_sharia, format_date_ordinal
            cached = load_cached_sharia()
            if cached is not None and not cached.empty:
                cached = enrich_cached_sharia(cached)
                rows = []
                for sym in symbols:
                    match = cached[cached["symbol"] == sym]
                    if not match.empty:
                        r = match.sort_values("report_period").iloc[-1]
                        rows.append({
                            "symbol": sym,
                            "name": r.get("name") or sym,
                            "Sharia": r.get("Sharia") or "Unknown",
                            "industry": r.get("industry"),
                            "sector": r.get("sector"),
                            "report_period": format_date_ordinal(r.get("report_period")),
                        })
                    else:
                        rows.append({"symbol": sym, "name": sym, "Sharia": "Unknown"})
                print_output(rows, fmt=args.format)
                return 0
        except Exception:
            pass
        print_output([{"symbol": s} for s in symbols], fmt=args.format)
        return 0

    if action == "add":
        if not args.symbols:
            print_error("Provide at least one symbol to add.", fmt=args.format)
            return 1
        symbols = _load()
        added = []
        for sym in args.symbols:
            sym = sym.strip().upper()
            if sym and sym not in symbols:
                symbols.append(sym)
                added.append(sym)
        _save(symbols)
        print_output({"ok": True, "added": added, "symbols": _load()}, fmt=args.format)
        return 0

    if action == "remove":
        if not args.symbols:
            print_error("Provide at least one symbol to remove.", fmt=args.format)
            return 1
        symbols = _load()
        to_remove = {s.strip().upper() for s in args.symbols}
        symbols = [s for s in symbols if s not in to_remove]
        _save(symbols)
        print_output({"ok": True, "removed": list(to_remove), "symbols": symbols}, fmt=args.format)
        return 0

    if action == "clear":
        _save([])
        print_output({"ok": True, "cleared": True, "symbols": []}, fmt=args.format)
        return 0

    return 1


def cmd_benchmarks(args):
    """List or show benchmark definitions."""
    from modules.portfolio import list_benchmarks, load_benchmark
    from core.output import print_output, print_error

    if args.action == "list":
        result = list_benchmarks()
        print_output(result, fmt=args.format)
        return 0

    if args.action == "show":
        if not args.benchmark_id:
            print_error("Provide a benchmark ID (e.g. nifty50, sensex30).", fmt=args.format)
            return 1
        try:
            data = load_benchmark(args.benchmark_id)
            print_output(data, fmt=args.format)
        except ValueError as e:
            print_error(str(e), fmt=args.format)
            return 1
        return 0

    return 1


def cmd_screener(args):
    """Multi-screen fundamental screener — rank and filter stocks by any combination of screens."""
    from core.output import print_output, print_error

    # --list-screens: show all registered screens
    if getattr(args, "list_screens", False):
        from modules.screener import SCREEN_CATALOG
        rows = [
            {
                "name": meta.name,
                "type": meta.screen_type,
                "description": meta.description,
                "score_range": meta.score_range,
                "pass_label": meta.pass_label,
            }
            for meta in SCREEN_CATALOG.values()
        ]
        print_output(rows, fmt=args.format)
        return 0

    # Resolve which screens to use
    screens_raw = getattr(args, "screens", None) or ""
    if screens_raw:
        screen_names = [s.strip().lower() for s in screens_raw.replace(",", " ").split() if s.strip()]
    else:
        screen_names = ["quality"]   # default: legacy quality screen (backward-compatible)

    # Validate screen names
    from modules.screener import SCREEN_CATALOG
    invalid = [s for s in screen_names if s not in SCREEN_CATALOG]
    if invalid:
        print_error(f"Unknown screen(s): {', '.join(invalid)}. Use --list-screens to see available.", fmt=args.format)
        return 1

    market = getattr(args, "market", "india")

    # --symbol: single stock scorecard
    if args.symbol:
        sym = args.symbol.strip().upper()
        from modules.screener import compute_screen

        if len(screen_names) == 1 and screen_names[0] == "quality" and not screens_raw:
            # Legacy behavior: full quality scorecard
            from modules.quality import compute_quality_score
            result = compute_quality_score(sym, force=args.force, market=market)
            if result.get("error"):
                print_error(f"{sym}: {result['error']}", fmt=args.format)
                return 1
            print_output(result, fmt=args.format)
            return 0

        # Multi-screen single stock view
        results = []
        for sname in screen_names:
            r = compute_screen(sname, sym, force=args.force, market=market)
            d = r.to_dict()
            if getattr(args, "verbose", False):
                results.append(d)
            else:
                results.append({
                    "screen": sname,
                    "score": d["score"],
                    "label": d["label"],
                    "passed": d["passed"],
                    "data_quality": d["data_quality"],
                    "error": d.get("error"),
                })
        print_output(results, fmt=args.format)
        return 0

    # --compute: batch compute selected screens
    if args.compute:
        symbols_raw = args.symbols or ""
        if symbols_raw:
            symbols = [s.strip().upper() for s in symbols_raw.replace(",", " ").split() if s.strip()]
        else:
            from modules.sharia import load_cached_sharia, enrich_cached_sharia
            cached = load_cached_sharia(market=market)
            if cached is None or cached.empty:
                print_error("No Sharia cache found. Run: ./cli.py compute sharia --missing", fmt=args.format)
                return 1
            cached = enrich_cached_sharia(cached)
            df = cached.sort_values(["symbol", "report_period"]).groupby("symbol").last().reset_index()
            df = df[df["Sharia"] == "Yes"]
            symbols = df["symbol"].tolist()

        if not symbols:
            print_error("No symbols to compute.", fmt=args.format)
            return 1

        from modules.screener import batch_compute_screen
        summary = {}
        for sname in screen_names:
            if not args.quiet:
                print(f"Computing '{sname}' for {len(symbols)} symbols ({args.workers} workers)…", file=sys.stderr)

            done_count = [0]

            def _progress(done, total, _sname=sname):
                done_count[0] = done
                if not args.quiet:
                    print(f"  {sname}: {done}/{total}", end="\r", file=sys.stderr)

            results = batch_compute_screen(sname, symbols, workers=args.workers, force=args.force, progress_cb=_progress, market=market)
            errors = [r["symbol"] for r in results if r.get("error")]
            summary[sname] = {"computed": len(results), "errors": errors, "error_count": len(errors)}
            if not args.quiet:
                print(f"  {sname}: done ({len(results)} computed, {len(errors)} errors)", file=sys.stderr)

        print_output(summary, fmt=args.format)
        return 0

    # --rank mode (or default list): multi-screen ranking view
    from modules.screener.cache import load_screen_cache
    from modules.quality import load_quality_cache

    # Optionally enrich with Sharia metadata
    sharia_lookup: dict = {}
    try:
        from modules.sharia import load_cached_sharia, enrich_cached_sharia
        cached_s = load_cached_sharia(market=market)
        if cached_s is not None and not cached_s.empty:
            cached_s = enrich_cached_sharia(cached_s)
            df_s = cached_s.sort_values(["symbol", "report_period"]).groupby("symbol").last().reset_index()
            sharia_lookup = {row["symbol"]: row for row in df_s.to_dict("records")}
    except Exception:
        pass

    # Load caches for all requested screens
    screen_caches: dict[str, dict] = {}
    for sname in screen_names:
        if sname == "quality":
            screen_caches["quality"] = load_quality_cache()
        else:
            screen_caches[sname] = load_screen_cache(sname)

    # Find symbols that have data in at least one screen
    all_symbols: set[str] = set()
    for cache in screen_caches.values():
        all_symbols.update(cache.keys())

    if not all_symbols:
        print_error(
            f"No cached data for screens: {', '.join(screen_names)}. Run: ./cli.py screener --compute --screens \"{','.join(screen_names)}\"",
            fmt=args.format,
        )
        return 1

    require_all_pass = getattr(args, "require_all_pass", False)
    rows = []

    for symbol in sorted(all_symbols):
        row: dict = {
            "symbol": symbol,
            "name": (sharia_lookup.get(symbol) or {}).get("name") or symbol,
            "Sharia": (sharia_lookup.get(symbol) or {}).get("Sharia") or "Unknown",
            "sector": (sharia_lookup.get(symbol) or {}).get("sector"),
        }

        # Sector filter
        if args.sector:
            sec = row["sector"] or ""
            if args.sector.lower() not in sec.lower():
                continue

        passes_all = True
        primary_score = None

        for sname in screen_names:
            cache = screen_caches.get(sname, {})
            entry = cache.get(symbol)

            if sname == "quality" and entry is not None:
                score = entry.get("total_score")
                label = entry.get("label")
                passed = (score or 0) >= 65
                row["quality"] = score
                row["quality_label"] = label
                if primary_score is None and score is not None:
                    primary_score = score
            elif entry is not None:
                score = entry.get("score")
                label = entry.get("label")
                passed = entry.get("passed", False)
                row[sname] = score
                row[f"{sname}_label"] = label
                if primary_score is None and score is not None and sname not in ("red_flags", "beneish_m"):
                    primary_score = score
            else:
                row[sname] = None
                row[f"{sname}_label"] = None
                passed = False

            if require_all_pass and not passed:
                passes_all = False

        if require_all_pass and not passes_all:
            continue

        # Min-score filter applies to primary (first) screen
        primary_entry = screen_caches.get(screen_names[0], {}).get(symbol)
        if args.min_score and primary_entry:
            score_val = primary_entry.get("total_score") if screen_names[0] == "quality" else primary_entry.get("score")
            if score_val is not None and score_val < args.min_score:
                continue

        row["_sort_score"] = primary_score or 0
        rows.append(row)

    rows.sort(key=lambda r: r.pop("_sort_score", 0), reverse=True)
    if args.top:
        rows = rows[:args.top]

    print_output(rows, fmt=args.format)
    return 0


def cmd_cache(args):
    """Cache status or management."""
    from core.cache import get_staleness, load_meta
    from core.output import print_output

    if args.action == "status":
        from modules.sharia import load_cached_sharia
        from modules.universe import load_universe

        tickers, _ = load_universe(market="india")
        cached = load_cached_sharia()
        sharia_staleness = get_staleness("sharia", max_age_hours=72)

        symbols_with_data = cached["symbol"].nunique() if cached is not None else 0

        print_output({
            "module": "sharia",
            "stale": sharia_staleness["stale"],
            "last_refresh": sharia_staleness["last_refresh"],
            "age_hours": sharia_staleness["oldest_hours"],
            "symbols_with_data": symbols_with_data,
            "symbols_missing": len(tickers) - symbols_with_data,
            "total_universe": len(tickers),
        }, fmt=args.format)
        return 0

    if args.action == "clear":
        from core.config import CACHE_DIR
        module = args.module or "all"
        if module == "sharia" or module == "all":
            cache_file = CACHE_DIR / "sharia_metrics.parquet"
            if cache_file.exists():
                cache_file.unlink()
                if not args.quiet:
                    print("Cleared sharia cache.", file=sys.stderr)
        print_output({"cleared": module}, fmt=args.format)
        return 0

    return 1


def cmd_import(args):
    """Import external data (e.g. BSE scrip list)."""
    from core.output import print_output, print_error
    from core.config import INPUT_DIR

    if args.type == "bse-scrips":
        import shutil
        src = Path(args.file)
        if not src.exists():
            print_error(f"File not found: {src}", fmt=args.format)
            return 1
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        dst = INPUT_DIR / "Equity.csv"
        shutil.copy2(src, dst)
        print_output({"imported": "bse-scrips", "path": str(dst)}, fmt=args.format)
        return 0

    if args.type == "nse-mcap":
        import shutil
        src = Path(args.file)
        if not src.exists():
            print_error(f"File not found: {src}", fmt=args.format)
            return 1
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        dst = INPUT_DIR / "Average_MCAP_NSE.xlsx"
        shutil.copy2(src, dst)
        print_output({"imported": "nse-mcap", "path": str(dst)}, fmt=args.format)
        return 0

    print_error(f"Unknown import type: {args.type}. Supported: bse-scrips, nse-mcap", fmt=args.format)
    return 1


def cmd_research(args):
    """View stored research or signal that web research is needed."""
    from core.output import print_output, print_error
    from modules.research import load_research, RESEARCH_SECTIONS

    symbol = args.symbol
    section = args.section  # None means all

    if args.view:
        data = load_research(symbol, section)
        if not data:
            label = f"{section} research" if section else "research"
            return print_error(f"No {label} for {symbol}", fmt=args.format)
        if section:
            return print_output(data, fmt=args.format)
        # All sections: show summary
        return print_output({
            "symbol": symbol,
            "sections_available": list(data.keys()),
            "sections": data,
        }, fmt=args.format)

    # Signal that web research is needed (exit code 2)
    sections = [section] if section else RESEARCH_SECTIONS
    print_output({
        "status": "needs_web_research",
        "symbol": symbol,
        "sections": sections,
        "needs_web_fetch": sections,
        "instructions": (
            "Use web search to research each section, then PUT to "
            f"/api/symbol/{symbol}/research/{{section}} with the structured JSON envelope."
        ),
    }, fmt=args.format)
    return 2


def cmd_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    if not args.quiet:
        print(f"Starting server on http://localhost:{args.port}", file=sys.stderr)
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    # Shared flags available on every subcommand (before or after subcommand name)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", "-f", choices=["json", "table", "csv"], default="table",
                        help="Output format (default: table)")
    common.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress output")

    parser = argparse.ArgumentParser(
        prog="invest",
        description="Investment Platform CLI — stock screening, analysis, and portfolio tools.",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- universe ---
    p = sub.add_parser("universe", help="List stock tickers", parents=[common])
    p.add_argument("--market", "-m", default="india", help="Market (default: india)")
    p.add_argument("--stats", action="store_true", help="Show counts only")
    p.add_argument("--exchange", "-e", help="Filter by exchange (NSE or BSE)")
    p.add_argument("--limit", "-n", type=int, help="Limit output rows")

    # --- sharia ---
    p = sub.add_parser("sharia", help="Sharia compliance status", parents=[common])
    p.add_argument("args", nargs="*", default=[],
                   help="'list' to show all compliant, or a stock symbol (e.g. TCS.NS or TCS, or AAPL)")
    p.add_argument("--periods", action="store_true", help="Show all periods for symbol")
    p.add_argument("--period", "-p", help="Filter by period label (e.g. '31st March 2025')")
    p.add_argument("--market", "-m", default="india", help="Market: india (default) or us")

    # --- compute ---
    p = sub.add_parser("compute", help="Compute metrics and update cache", parents=[common])
    p.add_argument("module", nargs="?", default="sharia", help="Module to compute (default: sharia)")
    p.add_argument("--symbols", "-s", help="Comma/space separated symbols to compute")
    p.add_argument("--portfolio", action="store_true", help="Compute default portfolio")
    p.add_argument("--missing", action="store_true", help="Compute symbols missing from cache")
    p.add_argument("--limit", "-n", type=int, help="Limit number of missing symbols")
    p.add_argument("--workers", "-w", type=int, default=5, help="Parallel workers (default: 5)")
    p.add_argument("--force", action="store_true", help="Re-fetch all from Yahoo Finance, even if cached")
    p.add_argument("--market", "-m", default="india", help="Market: india (default) or us")

    # --- lookup ---
    p = sub.add_parser("lookup", help="Detailed company data from Yahoo Finance", parents=[common])
    p.add_argument("symbol", help="Stock symbol")
    p.add_argument("--section", default="overview",
                   choices=["overview", "market", "financials", "valuation"],
                   help="Data section (default: overview)")
    p.add_argument("--force", action="store_true", help="Bypass cache")

    # --- compare ---
    p = sub.add_parser("compare", help="Compare multiple stocks", parents=[common])
    p.add_argument("symbols", nargs="+", help="Stock symbols to compare")

    # --- portfolio-index ---
    p = sub.add_parser("portfolio-index", help="Analyze a personal Sharia index portfolio", parents=[common])
    p.add_argument(
        "--holdings",
        required=True,
        help="Comma-separated SYMBOL:units[:price] entries, e.g. TCS:10,INFY:8,MARUTI.NS:2:11850",
    )
    p.add_argument(
        "--benchmark",
        choices=["nifty50", "sensex30"],
        default="nifty50",
        help="Benchmark to follow (default: nifty50)",
    )
    p.add_argument(
        "--sip",
        type=float,
        default=0.0,
        help="Optional fresh capital/SIP amount to allocate across underweights",
    )
    p.add_argument(
        "--allow-sells",
        action="store_true",
        help="Allow trims of compliant holdings that are above target; default is no-sell mode",
    )
    p.add_argument(
        "--max-buy-suggestions",
        type=int,
        default=10,
        help="Limit the number of new-money buy suggestions (default: 10)",
    )

    # --- cache ---
    p = sub.add_parser("cache", help="Cache management", parents=[common])
    p.add_argument("action", choices=["status", "clear"], help="Cache action")
    p.add_argument("--module", help="Module to clear (default: all)")

    # --- import ---
    p = sub.add_parser("import", help="Import external data files", parents=[common])
    p.add_argument("--type", "-t", required=True,
                   choices=["bse-scrips", "nse-mcap"],
                   help="Type of data to import")
    p.add_argument("--file", required=True, help="Path to the file to import")

    # --- research ---
    p = sub.add_parser("research", help="View or trigger web research for a stock", parents=[common])
    p.add_argument("symbol", help="Stock symbol (e.g. CUMMINSIND.NS)")
    p.add_argument("--section", "-s", choices=[
        "thesis", "industry", "business", "management",
        "esg", "estimates", "revenue", "catalysts",
    ], help="Specific section (default: all)")
    p.add_argument("--view", action="store_true", help="View stored research (don't trigger new)")

    # --- screener ---
    p = sub.add_parser("screener", help="Multi-screen fundamental screener — rank stocks by any combination of screens", parents=[common])
    p.add_argument("--symbol", "-s", help="Single stock multi-screen scorecard (e.g. TCS.NS)")
    p.add_argument("--compute", action="store_true", help="Batch compute selected screens and cache results")
    p.add_argument("--symbols", help="Comma/space separated symbols for --compute (default: all Sharia-compliant)")
    p.add_argument("--screens", help="Comma-separated screen names to use (default: quality). E.g. 'piotroski,altman_z,beneish_m'")
    p.add_argument("--list-screens", action="store_true", dest="list_screens", help="List all available screens with descriptions")
    p.add_argument("--rank", action="store_true", help="Rank mode: sort by first screen score (implied when not --symbol/--compute)")
    p.add_argument("--require-all-pass", action="store_true", dest="require_all_pass", help="Only show stocks where ALL selected screens pass their threshold")
    p.add_argument("--verbose", action="store_true", help="Show full breakdown per screen (for --symbol mode)")
    p.add_argument("--top", "-n", type=int, default=0, help="Limit output to top N stocks")
    p.add_argument("--min-score", type=int, default=0, help="Minimum score filter on first screen (0-100)")
    p.add_argument("--sector", help="Filter by sector (partial match, e.g. Technology)")
    p.add_argument("--workers", "-w", type=int, default=5, help="Parallel workers for --compute (default: 5)")
    p.add_argument("--force", action="store_true", help="Bypass cache and re-fetch from yfinance")
    p.add_argument("--market", "-m", default="india", help="Market: india (default) or us")

    # --- watchlist ---
    p = sub.add_parser("watchlist", help="Manage stock watchlist", parents=[common])
    p.add_argument("action", choices=["list", "add", "remove", "clear"],
                   help="Watchlist action")
    p.add_argument("symbols", nargs="*", default=[],
                   help="Symbol(s) for add/remove actions (e.g. TCS INFY RELIANCE)")

    # --- benchmarks ---
    p = sub.add_parser("benchmarks", help="List or inspect benchmark definitions", parents=[common])
    p.add_argument("action", choices=["list", "show"],
                   help="'list' to show all benchmarks, 'show' to inspect one")
    p.add_argument("benchmark_id", nargs="?", default=None,
                   help="Benchmark ID for 'show' action (e.g. nifty50, sensex30)")

    # --- serve ---
    p = sub.add_parser("serve", help="Start the web server", parents=[common])
    p.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p.add_argument("--reload", action="store_true", help="Auto-reload on changes")

    # --- portfolio ---
    pp = sub.add_parser("portfolio", help="Policy-aware portfolio analysis and sizing", parents=[common])
    port_sub = pp.add_subparsers(dest="port_action")

    pa = port_sub.add_parser("analyze", help="Gap analysis vs personal policy", parents=[common])
    pa.add_argument(
        "--holdings", required=True,
        help="Comma-separated SYMBOL:units[:price] entries, e.g. TCS.NS:9,INFY.NS:24",
    )

    ps = port_sub.add_parser("size", help="Position sizing for a new stock", parents=[common])
    ps.add_argument("--symbol", required=True, help="Symbol to size (e.g. MARUTI.NS)")
    ps.add_argument(
        "--holdings", required=True,
        help="Current holdings as SYMBOL:units[:price], e.g. TCS.NS:9,INFY.NS:24",
    )
    ps.add_argument("--sip", type=float, default=0.0, help="Fresh capital to deploy (₹)")

    # --- universe-suggest ---
    p = sub.add_parser(
        "universe-suggest",
        help="Sharia-compliant candidates for a sector + cap tier slot",
        parents=[common],
    )
    p.add_argument("--sector", required=True,
                   help="Sector keyword, e.g. 'Auto', 'Chemicals', 'Pharma'")
    p.add_argument("--cap", required=True, choices=["large", "mid", "small"],
                   help="Cap tier (large=rank 1-100, mid=101-250, small=251-500)")
    p.add_argument("--exclude", help="Comma-separated symbols to exclude (e.g. current holdings)")
    p.add_argument("--force-sharia", action="store_true", dest="force_sharia",
                   help="Compute Sharia for uncached symbols on-demand (slow)")
    p.add_argument("--max", type=int, default=30, help="Max candidates to return (default: 30)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "universe": cmd_universe,
        "sharia": cmd_sharia,
        "compute": cmd_compute,
        "lookup": cmd_lookup,
        "compare": cmd_compare,
        "portfolio-index": cmd_portfolio_index,
        "portfolio": cmd_portfolio,
        "universe-suggest": cmd_universe_suggest,
        "cache": cmd_cache,
        "import": cmd_import,
        "research": cmd_research,
        "screener": cmd_screener,
        "watchlist": cmd_watchlist,
        "benchmarks": cmd_benchmarks,
        "serve": cmd_serve,
    }

    handler = commands.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
