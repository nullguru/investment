# -*- coding: utf-8 -*-
"""
Broker order history importer.

Reads Zerodha/broker Excel exports (Stocks_Order_History_*.xlsx) and
converts them into Trade records, skipping any rows already imported
(matched by exchange_order_id stored in trade metadata).

Supported format:
  Row 5 onwards (0-indexed row 4) is the header:
  Stock name | Symbol | ISIN | Type | Quantity | Value | Exchange |
  Exchange Order Id | Execution date and time | Order status

Usage:
    from modules.trades.importer import import_from_xlsx
    result = import_from_xlsx(Path("raw_data/Stocks_Order_History_...xlsx"))
    # result: {"imported": N, "skipped": N, "errors": [...]}
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from modules.trades.ledger import load_trades, save_trades

# Default path (relative to repo root)
DEFAULT_XLSX_PATH = Path("raw_data/Stocks_Order_History_7394449057_01-05-2025_07-06-2026.xlsx")

_DATE_FORMATS = [
    "%d-%m-%Y %I:%M %p",   # 14-07-2025 10:03 AM
    "%d-%m-%Y %H:%M",      # 14-07-2025 10:03
    "%Y-%m-%d %H:%M:%S",
]


def _parse_date(raw: str) -> str:
    """Return ISO date string (YYYY-MM-DD) from broker datetime string."""
    raw = str(raw).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback: grab first 10 chars if looks like YYYY-MM-DD
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    raise ValueError(f"Cannot parse date: {raw!r}")


def _symbol_with_suffix(symbol: str, exchange: str) -> str:
    """Add yfinance suffix if missing.  NSE → .NS, BSE → .BO"""
    s = symbol.strip().upper()
    if "." in s:
        return s
    if exchange.upper() == "BSE":
        return s + ".BO"
    return s + ".NS"  # default NSE


def _build_trade(row: dict) -> dict:
    symbol = _symbol_with_suffix(row["symbol"], row["exchange"])
    quantity = float(row["quantity"])
    value = float(row["value"])
    price = round(value / quantity, 2) if quantity else 0.0
    date = _parse_date(row["execution_datetime"])
    action = str(row["type"]).upper()  # BUY | SELL

    trade_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": trade_id,
        "symbol": symbol,
        "action": action,
        "units": quantity,
        "price": price,
        "currency": "INR",
        "date": date,
        "status": "executed",
        "conviction": "medium",
        "pre_trade_check": {"imported": True, "skipped_reason": "historical import"},
        "reasoning": f"Imported from broker order history — {row.get('stock_name', symbol)}",
        "thesis_section": "",
        "risks_acknowledged": [],
        "exit_plan": {},
        "emotion_check": "neutral",
        "outcome_notes": "",
        "closed_at": "",
        # Broker metadata stored for deduplication
        "_import_meta": {
            "exchange_order_id": str(row.get("exchange_order_id", "")),
            "exchange": row.get("exchange", ""),
            "isin": row.get("isin", ""),
            "stock_name": row.get("stock_name", ""),
            "source": "broker_xlsx",
        },
        "created_at": now,
        "updated_at": now,
        "total_value": round(value, 2),
    }


def _existing_order_ids(trades: list[dict]) -> set[str]:
    ids: set[str] = set()
    for t in trades:
        meta = t.get("_import_meta", {})
        oid = meta.get("exchange_order_id", "")
        if oid:
            ids.add(str(oid))
    return ids


def import_from_xlsx(path: Path | None = None) -> dict:
    """
    Import trades from broker Excel export.

    Returns:
        {
            "imported": int,
            "skipped": int,
            "duplicate": int,
            "errors": [str],
            "trades": [dict]   # newly imported trade dicts
        }
    """
    if path is None:
        path = DEFAULT_XLSX_PATH

    path = Path(path)
    if not path.exists():
        return {"imported": 0, "skipped": 0, "duplicate": 0,
                "errors": [f"File not found: {path}"], "trades": []}

    # ── Parse Excel ───────────────────────────────────────────────────────────
    try:
        df = pd.read_excel(path, skiprows=4, engine="openpyxl")
        df.columns = [
            "stock_name", "symbol", "isin", "type", "quantity",
            "value", "exchange", "exchange_order_id", "execution_datetime", "order_status",
        ]
        # Drop header re-rows and empty rows
        df = df[df["symbol"].notna()]
        df = df[df["symbol"].astype(str).str.strip() != "Symbol"]
        df = df[df["type"].astype(str).str.upper().isin(["BUY", "SELL"])]
        df = df[df.get("order_status", pd.Series(["Executed"] * len(df))).astype(str).str.lower() == "executed"]
    except Exception as exc:
        return {"imported": 0, "skipped": 0, "duplicate": 0,
                "errors": [f"Failed to read Excel: {exc}"], "trades": []}

    # ── Load existing trades and find already-imported order IDs ──────────────
    existing = load_trades()
    known_order_ids = _existing_order_ids(existing)

    imported: list[dict] = []
    skipped = 0
    duplicate = 0
    errors: list[str] = []

    for _, row in df.iterrows():
        order_id = str(row.get("exchange_order_id", "")).strip()
        if order_id and order_id in known_order_ids:
            duplicate += 1
            continue

        try:
            trade = _build_trade(row.to_dict())
            imported.append(trade)
            if order_id:
                known_order_ids.add(order_id)
        except Exception as exc:
            skipped += 1
            errors.append(f"Row {row.get('symbol', '?')}: {exc}")

    if imported:
        # Merge: sort all trades chronologically after appending
        all_trades = existing + imported
        all_trades.sort(key=lambda t: t.get("date", ""), reverse=False)
        save_trades(all_trades)

    return {
        "imported": len(imported),
        "duplicate": duplicate,
        "skipped": skipped,
        "errors": errors,
        "trades": imported,
    }


def preview_xlsx(path: Path | None = None) -> dict:
    """Return parsed rows without writing to DB — for UI preview."""
    if path is None:
        path = DEFAULT_XLSX_PATH

    path = Path(path)
    if not path.exists():
        return {"rows": [], "error": f"File not found: {path}"}

    try:
        df = pd.read_excel(path, skiprows=4, engine="openpyxl")
        df.columns = [
            "stock_name", "symbol", "isin", "type", "quantity",
            "value", "exchange", "exchange_order_id", "execution_datetime", "order_status",
        ]
        df = df[df["symbol"].notna()]
        df = df[df["symbol"].astype(str).str.strip() != "Symbol"]
        df = df[df["type"].astype(str).str.upper().isin(["BUY", "SELL"])]
    except Exception as exc:
        return {"rows": [], "error": str(exc)}

    existing = load_trades()
    known_order_ids = _existing_order_ids(existing)

    rows = []
    for _, row in df.iterrows():
        order_id = str(row.get("exchange_order_id", "")).strip()
        is_dup = order_id in known_order_ids

        try:
            date = _parse_date(str(row.get("execution_datetime", "")))
        except Exception:
            date = str(row.get("execution_datetime", ""))

        q = float(row.get("quantity", 0) or 0)
        v = float(row.get("value", 0) or 0)

        rows.append({
            "symbol": _symbol_with_suffix(str(row.get("symbol", "")), str(row.get("exchange", "NSE"))),
            "stock_name": str(row.get("stock_name", "")),
            "action": str(row.get("type", "")).upper(),
            "quantity": q,
            "value": round(v, 2),
            "price": round(v / q, 2) if q else 0.0,
            "exchange": str(row.get("exchange", "")),
            "date": date,
            "order_id": order_id,
            "already_imported": is_dup,
        })

    return {"rows": rows, "error": None}
