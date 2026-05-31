# -*- coding: utf-8 -*-
"""
Generic cache infrastructure: parquet I/O and metadata tracking.
Tracks per-module, per-symbol refresh timestamps in cache/meta.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from core.config import CACHE_DIR

META_PATH = CACHE_DIR / "meta.json"


# ---- Parquet I/O ----

def load_parquet(path: Path) -> Optional[pd.DataFrame]:
    """Load a parquet file. Returns None if missing or unreadable."""
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame to parquet. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


# ---- Cache metadata ----

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_meta() -> Dict[str, Any]:
    """Load cache/meta.json. Returns empty structure if missing."""
    if not META_PATH.exists():
        return {"modules": {}}
    try:
        with open(META_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if "modules" not in data:
            data["modules"] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {"modules": {}}


def save_meta(meta: Dict[str, Any]) -> None:
    """Persist cache/meta.json."""
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def mark_refreshed(
    module: str,
    symbols: Optional[List[str]] = None,
    source: str = "yfinance",
) -> None:
    """Record that data was refreshed for a module (and optionally specific symbols)."""
    meta = load_meta()
    if module not in meta["modules"]:
        meta["modules"][module] = {"last_refresh": None, "symbols": {}}
    mod = meta["modules"][module]
    now = _now_iso()
    mod["last_refresh"] = now
    if symbols:
        for s in symbols:
            mod["symbols"][s] = {"last_refresh": now, "source": source}
    save_meta(meta)


def get_staleness(module: str, max_age_hours: float = 72) -> Dict[str, Any]:
    """
    Return staleness info for a module.
    Returns: {stale, last_refresh, oldest_hours, symbol_count}
    """
    meta = load_meta()
    mod = meta.get("modules", {}).get(module, {})
    last_refresh = mod.get("last_refresh")
    symbols = mod.get("symbols", {})

    if not last_refresh:
        return {
            "stale": True,
            "last_refresh": None,
            "oldest_hours": None,
            "symbol_count": len(symbols),
        }

    now = datetime.now(timezone.utc)
    try:
        lr = datetime.fromisoformat(last_refresh)
        if lr.tzinfo is None:
            lr = lr.replace(tzinfo=timezone.utc)
        hours = (now - lr).total_seconds() / 3600
    except (ValueError, TypeError):
        hours = float("inf")

    return {
        "stale": hours > max_age_hours,
        "last_refresh": last_refresh,
        "oldest_hours": round(hours, 1),
        "symbol_count": len(symbols),
    }


def is_stale(module: str, symbol: str, max_age_hours: float = 24) -> bool:
    """Check if a specific symbol's data is stale."""
    meta = load_meta()
    mod = meta.get("modules", {}).get(module, {})
    sym_info = mod.get("symbols", {}).get(symbol)
    if not sym_info or not sym_info.get("last_refresh"):
        return True
    now = datetime.now(timezone.utc)
    try:
        lr = datetime.fromisoformat(sym_info["last_refresh"])
        if lr.tzinfo is None:
            lr = lr.replace(tzinfo=timezone.utc)
        return (now - lr).total_seconds() / 3600 > max_age_hours
    except (ValueError, TypeError):
        return True
