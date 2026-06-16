# -*- coding: utf-8 -*-
"""
Deployment scenario engine.

Given current holdings, a policy analysis result (with gap candidates), and
a list of new-money amounts, returns a prioritised buy list for each amount.

Priority order:
  1. Replace non-Sharia holdings with best compliant alternative (same sector)
  2. Fill policy sector gaps (high-priority gaps first)
  3. Top up underweight compliant existing holdings
  4. Any remainder → most underweight compliant holding

A buy is skipped if the allocated amount is less than one unit price (stock too
expensive for the slice).
"""

from __future__ import annotations

from typing import Optional


def _round2(v: float) -> float:
    return round(v, 2)


def _weight_pct(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(value / total * 1000) / 10  # one decimal


def compute_deployment_scenarios(
    holdings: list[dict],
    policy_result: dict,
    amounts: list[int] | None = None,
    market: str = "india",
) -> list[dict]:
    """
    holdings      – list of {symbol, units, current_price, value, sharia, ...}
                    as returned by the enriched policy analysis
    policy_result – full dict from analyze_portfolio (includes 'candidates',
                    'stock_weights', 'summary', etc.)
    amounts       – new-cash amounts to model (default: 25k/50k/75k/1L)

    Returns a list of scenario dicts, one per amount.
    """
    if amounts is None:
        amounts = [25_000, 50_000, 75_000, 100_000]

    # ── Index holdings by symbol ──────────────────────────────────────────────
    holding_map: dict[str, dict] = {h["symbol"]: h for h in holdings}

    def current_value(symbol: str) -> float:
        h = holding_map.get(symbol, {})
        v = h.get("value")
        return float(v) if v else 0.0

    def unit_price(symbol: str) -> Optional[float]:
        h = holding_map.get(symbol, {})
        p = h.get("price") or h.get("current_price")
        return float(p) if p else None

    current_total = policy_result.get("summary", {}).get("total_value", 0.0) or 0.0
    n = len(holdings)
    target_weight_pct = min(8.0, 100.0 / max(n, 12))  # ~equal weight, max 8 %

    # ── Identify non-Sharia sells (same across all scenarios) ────────────────
    sells: list[dict] = []
    sale_proceeds = 0.0
    for h in holdings:
        if h.get("sharia") == "No":
            val = h.get("value") or 0.0
            sells.append({
                "symbol": h["symbol"],
                "amount": float(val),
                "replacement": _best_replacement(h["symbol"], policy_result, holding_map),
            })
            sale_proceeds += float(val)

    # ── Gap candidates (high priority first) ─────────────────────────────────
    gap_candidates: list[dict] = []   # {symbol, sector, priority, unit_price}
    for cand in policy_result.get("candidates", []):
        if cand.get("priority") == "blocked":
            continue
        best = next((o for o in (cand.get("options") or []) if o.get("sharia_status") == "Yes"), None)
        if best:
            gap_candidates.append({
                "symbol": best["symbol"],
                "sector": cand["sector_gap"],
                "priority": cand.get("priority", "normal"),
                "unit_price": best.get("current_price"),
            })

    # Sort: high priority first
    gap_candidates.sort(key=lambda c: 0 if c["priority"] == "high" else 1)

    # ── Build one scenario per amount ─────────────────────────────────────────
    scenarios = []
    for new_amount in amounts:
        deployable = new_amount + sale_proceeds
        new_total = current_total + new_amount
        remaining = deployable
        buys: list[dict] = []

        def sym_in_buys(symbol: str) -> bool:
            return any(b["symbol"] == symbol for b in buys)

        def _affordable(amount: float, symbol: str, candidate_price: Optional[float] = None) -> bool:
            price = candidate_price or unit_price(symbol)
            return (price is None) or (amount >= price)

        # 1. Replace non-Sharia with best compliant alternative
        for sale in sells:
            if remaining <= 0:
                break
            rep = sale["replacement"]
            if not rep:
                continue
            cur_val = current_value(rep["symbol"])
            cur_w = _weight_pct(cur_val, new_total)
            buy_amt = min(sale["amount"], remaining, new_total * 0.08 - cur_val)
            if not _affordable(buy_amt, rep["symbol"]):
                continue
            if buy_amt > 500:
                new_w = _weight_pct(cur_val + buy_amt, new_total)
                buys.append({
                    "symbol": rep["symbol"].replace(".NS", "").replace(".BO", ""),
                    "amount": round(buy_amt),
                    "reason": f"↔ Replace {sale['symbol'].replace('.NS', '').replace('.BO', '')}",
                    "current_weight": cur_w,
                    "new_weight": new_w,
                })
                remaining -= buy_amt

        # 2. Fill sector gaps
        if remaining > 500:
            num_gaps = max(len(gap_candidates), 1)
            for cand in gap_candidates:
                if remaining < 500:
                    break
                if sym_in_buys(cand["symbol"]):
                    continue
                cur_val = current_value(cand["symbol"])
                cur_w = _weight_pct(cur_val, new_total)
                if cur_w >= 8.0:
                    continue
                slice_amt = round(min(remaining / num_gaps, new_total * 0.08 - cur_val, remaining))
                if not _affordable(slice_amt, cand["symbol"], cand.get("unit_price")):
                    continue
                if slice_amt > 500:
                    new_w = _weight_pct(cur_val + slice_amt, new_total)
                    label = ("🎯 Gap fill" if cand["priority"] == "high" else "↗ Gap fill") + f" — {cand['sector']}"
                    buys.append({
                        "symbol": cand["symbol"].replace(".NS", "").replace(".BO", ""),
                        "amount": slice_amt,
                        "reason": label,
                        "current_weight": cur_w,
                        "new_weight": new_w,
                    })
                    remaining -= slice_amt

        # 3. Top up underweight compliant existing holdings
        if remaining > 500:
            underweight = sorted(
                [
                    h for h in holdings
                    if h.get("sharia") == "Yes"
                    and not sym_in_buys(h["symbol"].replace(".NS", "").replace(".BO", ""))
                ],
                key=lambda h: _weight_pct(h.get("value") or 0, new_total),
            )
            for h in underweight:
                if remaining < 500:
                    break
                cur_val = float(h.get("value") or 0)
                cur_w = _weight_pct(cur_val, new_total)
                if cur_w >= target_weight_pct:
                    continue
                deficit = (target_weight_pct - cur_w) / 100.0 * new_total
                buy_amt = round(min(deficit, remaining, new_total * 0.08 - cur_val))
                if not _affordable(buy_amt, h["symbol"]):
                    continue
                if buy_amt > 500:
                    new_w = _weight_pct(cur_val + buy_amt, new_total)
                    buys.append({
                        "symbol": h["symbol"].replace(".NS", "").replace(".BO", ""),
                        "amount": buy_amt,
                        "reason": f"↑ Underweight ({cur_w}%)",
                        "current_weight": cur_w,
                        "new_weight": new_w,
                    })
                    remaining -= buy_amt

        # 4. Leftover → most underweight compliant holding
        if remaining > 500:
            already = {b["symbol"] for b in buys}
            fallback = sorted(
                [h for h in holdings if h.get("sharia") == "Yes"
                 and h["symbol"].replace(".NS", "").replace(".BO", "") not in already],
                key=lambda h: _weight_pct(h.get("value") or 0, new_total),
            )
            if fallback:
                h = fallback[0]
                cur_val = float(h.get("value") or 0)
                cur_w = _weight_pct(cur_val, new_total)
                new_w = _weight_pct(cur_val + remaining, new_total)
                buys.append({
                    "symbol": h["symbol"].replace(".NS", "").replace(".BO", ""),
                    "amount": round(remaining),
                    "reason": "↑ Best underweight",
                    "current_weight": cur_w,
                    "new_weight": new_w,
                })
                remaining = 0

        scenarios.append({
            "idx": len(scenarios),
            "new_amount": new_amount,
            "label": _format_inr(new_amount),
            "deployable": round(deployable),
            "new_total": round(new_total),
            "sells": [
                {"symbol": s["symbol"].replace(".NS", "").replace(".BO", ""), "amount": round(s["amount"])}
                for s in sells
            ],
            "buys": buys,
            "remaining": round(remaining),
        })

    return scenarios


def _best_replacement(symbol: str, policy_result: dict, holding_map: dict) -> Optional[dict]:
    """Find best Sharia-compliant replacement for a non-compliant symbol."""
    existing = set(holding_map.keys())
    for cand in policy_result.get("candidates", []):
        for opt in (cand.get("options") or []):
            if opt.get("sharia_status") == "Yes" and opt["symbol"] not in existing:
                return {"symbol": opt["symbol"]}
    return None


def _format_inr(amount: int) -> str:
    if amount >= 100_000:
        return f"₹{amount // 100_000},{(amount % 100_000) // 1000:02d},000"
    return f"₹{amount // 1000:,},000".replace(",", ",")
