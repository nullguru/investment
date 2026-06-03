# -*- coding: utf-8 -*-
"""
Pre-trade agent check.

Before committing a trade the agent runs this to surface:
  1. Sharia compliance status (hard block if non-compliant on BUY)
  2. Quality score (0-100)
  3. Red flag count (0-8)
  4. Piotroski F-Score
  5. Price vs 200 DMA  (entry timing signal)
  6. DCF margin of safety at proposed price
  7. Research thesis summary (if available)
  8. Existing position size

Returns a PreTradeReport dict ready to embed in the Trade record.
"""

from __future__ import annotations

import math
from typing import Optional


def run_pretrade_check(
    symbol: str,
    action: str,          # "BUY" | "SELL" | "PARTIAL_SELL"
    price: float,
    market: str = "india",
) -> dict:
    """
    Collect all pre-trade signals for symbol at the given price.
    Runs fast (uses caches; does NOT force-refresh yfinance).
    """
    from modules.sharia import load_cached_sharia, effective_sharia
    from modules.quality import load_quality_cache
    from modules.screener.registry import compute_screen
    from modules.market import get_section_data
    from modules.research import load_research
    from modules.trades.ledger import get_open_positions

    report: dict = {
        "symbol": symbol,
        "action": action,
        "check_price": price,
        "sharia_status": None,
        "sharia_detail": {},
        "quality_score": None,
        "quality_label": None,
        "red_flag_count": None,
        "red_flags_detail": [],
        "piotroski_score": None,
        "vs_200dma_pct": None,
        "dcf_mos_pct": None,
        "thesis_snippet": None,
        "current_position": None,
        "warnings": [],
        "blocks": [],           # hard stops (non-compliant BUY, etc.)
    }

    # ── 1. Sharia ────────────────────────────────────────────────────────────
    try:
        df = load_cached_sharia(market)
        if df is not None:
            rows = df[df["symbol"] == symbol]
            if not rows.empty:
                latest = rows.sort_values("report_period").iloc[-1]
                raw = effective_sharia(latest.get("Sharia"), latest.get("industry_compliant"))
                # Normalize raw 'Yes'/'No'/'Unknown' to display labels
                _map = {"Yes": "Compliant", "No": "Non-Compliant", "Unknown": "Unknown"}
                status = _map.get(str(raw), str(raw))
                report["sharia_status"] = status
                report["sharia_detail"] = {
                    "debt_to_equity": _safe(latest.get("debt_to_equity_ratio")),
                    "cash_to_assets": _safe(latest.get("cash_to_assets_pct")),
                    "non_halal_revenue": _safe(latest.get("other_revenue_to_revenue_pct")),
                    "industry_compliant": bool(latest.get("industry_compliant", True)),
                    "period": str(latest.get("report_period", "")),
                }
                if action == "BUY" and status not in ("Compliant", "Doubtful"):
                    report["blocks"].append(
                        f"Sharia status is '{status}' — BUY blocked. Consider exiting existing position instead."
                    )
            else:
                report["warnings"].append("No Sharia data cached for this symbol — compute first.")
    except Exception as e:
        report["warnings"].append(f"Sharia check failed: {e}")

    # ── 2. Quality score ─────────────────────────────────────────────────────
    try:
        cache = load_quality_cache()
        if symbol in cache:
            q = cache[symbol]
            report["quality_score"] = q.get("total_score")
            report["quality_label"] = q.get("label")
            if q.get("total_score") is not None and q["total_score"] < 35:
                report["warnings"].append(f"Quality score is {q['total_score']}/100 ({q.get('label','Poor')}) — below acceptable threshold.")
    except Exception as e:
        report["warnings"].append(f"Quality check failed: {e}")

    # ── 3. Red flags ─────────────────────────────────────────────────────────
    try:
        from modules.screener.cache import load_screen_cache
        rf_cache = load_screen_cache("red_flags")
        if symbol in rf_cache:
            score = rf_cache[symbol].get("score", 0)
            detail = rf_cache[symbol].get("flags", [])
            report["red_flag_count"] = score
            report["red_flags_detail"] = detail
            if score >= 3:
                report["warnings"].append(f"{score} red flags detected: {', '.join(detail[:3])}.")
    except Exception as e:
        report["warnings"].append(f"Red flags check failed: {e}")

    # ── 4. Piotroski ─────────────────────────────────────────────────────────
    try:
        from modules.screener.cache import load_screen_cache
        p_cache = load_screen_cache("piotroski")
        if symbol in p_cache:
            report["piotroski_score"] = p_cache[symbol].get("score")
    except Exception:
        pass

    # ── 5. Price vs 200 DMA ──────────────────────────────────────────────────
    try:
        mkt = get_section_data(symbol, "market", market=market)
        dma200 = _safe(mkt.get("twoHundredDayAverage"))
        if dma200 and dma200 > 0:
            vs_dma = (price - dma200) / dma200 * 100
            report["vs_200dma_pct"] = round(vs_dma, 2)
            if action == "BUY" and vs_dma > 15:
                report["warnings"].append(f"Price is {vs_dma:+.1f}% above 200 DMA — elevated entry risk.")
            if action in ("SELL", "PARTIAL_SELL") and vs_dma < -20:
                report["warnings"].append(f"Price is {vs_dma:.1f}% below 200 DMA — consider if this is forced selling.")
    except Exception as e:
        report["warnings"].append(f"Price/DMA check failed: {e}")

    # ── 6. DCF margin of safety ──────────────────────────────────────────────
    try:
        val = get_section_data(symbol, "valuation", market=market)
        fin = get_section_data(symbol, "financials", market=market)
        fcf = _safe(fin.get("freeCashflow"))
        shares = _safe(val.get("sharesOutstanding")) or _safe(fin.get("sharesOutstanding"))
        if fcf and shares and shares > 0 and price > 0:
            # Simple single-stage DCF: FCF × (1+g) / (wacc - g) / shares
            g = 0.10   # 10% growth assumption
            wacc = 0.12
            if wacc > g:
                intrinsic = (fcf * (1 + g)) / (wacc - g) / shares
                mos = (intrinsic - price) / price * 100
                report["dcf_mos_pct"] = round(mos, 1)
                if action == "BUY" and mos < -20:
                    report["warnings"].append(f"DCF margin of safety is {mos:.1f}% at ₹{price:.0f} — appears overvalued.")
    except Exception as e:
        report["warnings"].append(f"DCF check failed: {e}")

    # ── 7. Thesis snippet ────────────────────────────────────────────────────
    try:
        research = load_research(symbol)
        if research and "thesis" in research:
            sec = research["thesis"]
            body = sec.get("body", "") or sec.get("summary", "") or str(sec)
            report["thesis_snippet"] = body[:400] if isinstance(body, str) else None
    except Exception:
        pass

    # ── 8. Existing position ─────────────────────────────────────────────────
    try:
        positions = get_open_positions()
        sym_up = symbol.upper()
        if sym_up in positions:
            pos = positions[sym_up]
            report["current_position"] = {
                "units": pos["units"],
                "avg_cost": round(pos["avg_cost"], 2),
                "total_invested": round(pos["total_invested"], 2),
                "unrealized_pnl_pct": round((price - pos["avg_cost"]) / pos["avg_cost"] * 100, 2) if pos["avg_cost"] > 0 else None,
            }
            if action == "SELL" and pos["units"] == 0:
                report["blocks"].append("No open position in the ledger to sell.")
    except Exception:
        pass

    return report


def _safe(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None
