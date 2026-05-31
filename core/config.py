# -*- coding: utf-8 -*-
"""
Project configuration: paths, environment overrides.
Domain-agnostic — no Sharia or market-specific constants here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

# Project root (parent of core/)
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.environ.get("FIN_CACHE_PATH", BASE_DIR / "cache"))
DB_DIR = Path(os.environ.get("FIN_DB_PATH", BASE_DIR / "db"))
INPUT_DIR = Path(os.environ.get("FIN_INPUT_PATH", BASE_DIR / "input"))
OUTPUT_DIR = Path(os.environ.get("FIN_OUTPUT_PATH", BASE_DIR / "output"))


def get_config() -> Dict[str, Any]:
    """Return project-wide config. Ensures directories exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "base_dir": BASE_DIR,
        "cache_dir": CACHE_DIR,
        "db_dir": DB_DIR,
        "input_dir": INPUT_DIR,
        "output_dir": OUTPUT_DIR,
    }
