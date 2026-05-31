# -*- coding: utf-8 -*-
"""Per-screen JSON cache management."""

from __future__ import annotations

import json

from core.config import DB_DIR


def _cache_path(screen_name: str):
    return DB_DIR / f"screener_{screen_name}.json"


def load_screen_cache(screen_name: str) -> dict:
    """Return {symbol: result_dict} for a given screen."""
    path = _cache_path(screen_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_screen_cache(screen_name: str, new_results: dict) -> None:
    """Merge new_results into existing cache and persist."""
    existing = load_screen_cache(screen_name)
    existing.update(new_results)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(screen_name).write_text(
        json.dumps(existing, indent=2, default=str), encoding="utf-8"
    )


def get_cached_result(screen_name: str, symbol: str) -> dict | None:
    return load_screen_cache(screen_name).get(symbol)


def cache_result(result_dict: dict) -> None:
    save_screen_cache(result_dict["screen_name"], {result_dict["symbol"]: result_dict})
