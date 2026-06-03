# -*- coding: utf-8 -*-
"""
Trade ledger — append-only log of every buy/sell decision.

Each trade record stores:
  - The transaction itself (symbol, action, units, price)
  - Pre-trade health check snapshot (Sharia, quality, red flags, DCF MOS)
  - Reasoning (why), risks acknowledged, exit plan
  - Emotion check (psychological self-audit)
  - Status: planned | executed | cancelled

Storage: db/trades.json  →  list of trade dicts (newest-first after load)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.config import DB_DIR

TRADES_PATH = DB_DIR / "trades.json"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    symbol: str
    action: str                        # "BUY" | "SELL" | "PARTIAL_SELL"
    units: float
    price: float
    currency: str = "INR"
    date: str = ""                     # YYYY-MM-DD, defaults to today
    status: str = "planned"            # "planned" | "executed" | "cancelled"
    conviction: str = "medium"         # "low" | "medium" | "high"

    # Pre-trade snapshot (filled by agent check)
    pre_trade_check: dict = field(default_factory=dict)

    # Decision quality
    reasoning: str = ""
    thesis_section: str = ""           # which research section drove this
    risks_acknowledged: list = field(default_factory=list)
    exit_plan: dict = field(default_factory=dict)
    emotion_check: str = "patient"     # "fearful" | "greedy" | "patient" | "uncertain"

    # Outcome tracking (filled later)
    outcome_notes: str = ""
    closed_at: str = ""                # ISO timestamp when position fully closed

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @property
    def total_value(self) -> float:
        return round(self.units * self.price, 2)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_value"] = self.total_value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Trade":
        d = {k: v for k, v in d.items() if k != "total_value"}
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_trades() -> list[dict]:
    """Load all trades. Returns list of dicts, newest first."""
    if not TRADES_PATH.exists():
        return []
    try:
        trades = json.loads(TRADES_PATH.read_text(encoding="utf-8"))
        return sorted(trades, key=lambda t: t.get("created_at", ""), reverse=True)
    except (json.JSONDecodeError, OSError):
        return []


def save_trades(trades: list[dict]) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    # Always save sorted by date desc
    ordered = sorted(trades, key=lambda t: t.get("date", "") + t.get("created_at", ""), reverse=True)
    TRADES_PATH.write_text(json.dumps(ordered, indent=2, default=str), encoding="utf-8")


def add_trade(trade: Trade) -> dict:
    """Append a trade to the ledger. Returns the saved dict."""
    trades = load_trades()
    d = trade.to_dict()
    trades.append(d)
    save_trades(trades)
    return d


def update_trade(trade_id: str, updates: dict) -> dict | None:
    """Update fields on an existing trade by id. Returns updated dict or None."""
    trades = load_trades()
    for t in trades:
        if t.get("id") == trade_id:
            t.update(updates)
            t["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_trades(trades)
            return t
    return None


def delete_trade(trade_id: str) -> bool:
    """Delete a trade by id. Returns True if found and deleted."""
    trades = load_trades()
    before = len(trades)
    trades = [t for t in trades if t.get("id") != trade_id]
    if len(trades) < before:
        save_trades(trades)
        return True
    return False


def get_trades_for_symbol(symbol: str) -> list[dict]:
    """All trades for a symbol, newest first."""
    return [t for t in load_trades() if t.get("symbol", "").upper() == symbol.upper()]


# ---------------------------------------------------------------------------
# Position & P&L helpers
# ---------------------------------------------------------------------------

def get_open_positions() -> dict[str, dict]:
    """
    Derive current holdings from the ledger using AVCO (average cost) method.

    Returns {symbol: {units, avg_cost, total_invested, currency}}
    Only includes symbols where net units > 0 after all executed trades.
    """
    positions: dict[str, dict] = {}

    # Process in chronological order (oldest first)
    trades = sorted(load_trades(), key=lambda t: t.get("date", "") + t.get("created_at", ""))

    for t in trades:
        if t.get("status") != "executed":
            continue

        sym = t["symbol"].upper()
        action = t.get("action", "BUY").upper()
        units = float(t.get("units", 0))
        price = float(t.get("price", 0))
        currency = t.get("currency", "INR")

        if sym not in positions:
            positions[sym] = {"units": 0.0, "avg_cost": 0.0, "total_invested": 0.0, "currency": currency}

        pos = positions[sym]

        if action == "BUY":
            new_invested = pos["total_invested"] + units * price
            new_units = pos["units"] + units
            pos["avg_cost"] = new_invested / new_units if new_units > 0 else 0
            pos["units"] = new_units
            pos["total_invested"] = new_invested

        elif action in ("SELL", "PARTIAL_SELL"):
            sold = min(units, pos["units"])
            # AVCO: reduce invested proportionally
            if pos["units"] > 0:
                pos["total_invested"] -= (sold / pos["units"]) * pos["total_invested"]
            pos["units"] = max(0, pos["units"] - sold)
            if pos["units"] == 0:
                pos["total_invested"] = 0.0
                pos["avg_cost"] = 0.0

    # Remove fully closed positions
    return {sym: p for sym, p in positions.items() if p["units"] > 0.001}


def compute_realized_pnl() -> list[dict]:
    """
    Compute realized P&L per sell trade using AVCO cost at time of sale.

    Returns list of {symbol, date, units_sold, sell_price, avg_cost_at_sale,
                     realized_pnl, pnl_pct, holding_days}
    """
    results = []
    running: dict[str, dict] = {}  # same as get_open_positions but tracked per trade

    trades = sorted(load_trades(), key=lambda t: t.get("date", "") + t.get("created_at", ""))

    for t in trades:
        if t.get("status") != "executed":
            continue

        sym = t["symbol"].upper()
        action = t.get("action", "BUY").upper()
        units = float(t.get("units", 0))
        price = float(t.get("price", 0))

        if sym not in running:
            running[sym] = {"units": 0.0, "avg_cost": 0.0, "total_invested": 0.0, "first_buy": t.get("date")}

        pos = running[sym]

        if action == "BUY":
            new_invested = pos["total_invested"] + units * price
            new_units = pos["units"] + units
            pos["avg_cost"] = new_invested / new_units if new_units > 0 else 0
            pos["units"] = new_units
            pos["total_invested"] = new_invested

        elif action in ("SELL", "PARTIAL_SELL"):
            cost_basis = pos["avg_cost"]
            sold = min(units, pos["units"])
            pnl = sold * (price - cost_basis)
            pnl_pct = ((price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

            # Holding days
            try:
                buy_d = datetime.strptime(pos["first_buy"], "%Y-%m-%d")
                sell_d = datetime.strptime(t["date"], "%Y-%m-%d")
                holding_days = (sell_d - buy_d).days
            except Exception:
                holding_days = None

            results.append({
                "symbol": sym,
                "date": t["date"],
                "trade_id": t.get("id"),
                "units_sold": sold,
                "sell_price": price,
                "avg_cost_at_sale": round(cost_basis, 2),
                "realized_pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "holding_days": holding_days,
            })

            if pos["units"] > 0:
                pos["total_invested"] -= (sold / pos["units"]) * pos["total_invested"]
            pos["units"] = max(0, pos["units"] - sold)

    return results
