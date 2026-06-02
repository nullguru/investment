# -*- coding: utf-8 -*-
"""
Field gap tracking: records which "wanted" fields are missing from the data provider.

When a field is null in yfinance responses, it's tagged as not_found_in_api.
The AI research layer can then attempt to fill these gaps.

Storage: db/field_gaps.json  →  {symbol: {section: {field: gap_info}}}
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.config import DB_DIR

FIELD_GAPS_PATH = DB_DIR / "field_gaps.json"

# Fields we WANT but yfinance often cannot supply for Indian/global stocks.
# Keyed by section name → list of field names.
ENRICHABLE_FIELDS: dict[str, list[str]] = {
    "overview": [
        "pledgedSharesPct",        # Pledged shares by promoters (critical for India)
        "boardSize",               # Number of board directors
        "boardIndependencePct",    # % independent directors
        "promoterHolding",         # Promoter stake (yfinance uses heldPercentInsiders as proxy)
        "managementTurnoverRisk",  # Recent key mgmt changes
        "relatedPartyTransactions",# RPT as % of revenue
    ],
    "financials": [
        "returnOnCapitalEmployed",  # ROCE — often absent in yfinance
        "freeCashFlowYield",        # FCF yield
        "workingCapitalDays",       # Cash conversion cycle proxy
    ],
    "market": [
        "shortInterestPct",         # Short interest — not available for Indian stocks
        "institutionalOwnershipChange",  # QoQ change in institutional holding
    ],
}


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def load_field_gaps() -> dict:
    """Load all field gaps. Returns {symbol: {section: {field: gap_info}}}."""
    if not FIELD_GAPS_PATH.exists():
        return {}
    try:
        return json.loads(FIELD_GAPS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_field_gaps(gaps: dict) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    FIELD_GAPS_PATH.write_text(
        json.dumps(gaps, indent=2, default=str), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def record_field_gaps(symbol: str, section: str, section_data: dict) -> dict:
    """
    Check which enrichable fields for this section are missing in section_data.
    Persist the gap record and return {field: gap_info} for this section.

    Called automatically after every yfinance section fetch.
    """
    wanted = ENRICHABLE_FIELDS.get(section, [])
    if not wanted or section_data.get("error"):
        return {}

    gaps = load_field_gaps()
    sym_gaps = gaps.setdefault(symbol, {})
    sec_gaps = sym_gaps.setdefault(section, {})
    now = datetime.now(timezone.utc).isoformat()

    changed = False
    for field in wanted:
        val = section_data.get(field)
        if val is None:
            # Field missing — record gap if not already there
            if field not in sec_gaps:
                sec_gaps[field] = {
                    "status": "not_found_in_api",
                    "provider": "yfinance",
                    "checked_at": now,
                    "filled_by": None,   # will be set to 'research' when AI fills it
                    "filled_at": None,
                }
                changed = True
        else:
            # Field now available — remove gap if it was there
            if field in sec_gaps and sec_gaps[field].get("filled_by") is None:
                del sec_gaps[field]
                changed = True

    if changed:
        save_field_gaps(gaps)

    return sec_gaps


def mark_field_filled(symbol: str, section: str, field: str, source: str = "research") -> None:
    """Mark a previously missing field as now filled by AI research (or another source)."""
    gaps = load_field_gaps()
    entry = gaps.get(symbol, {}).get(section, {}).get(field)
    if entry:
        entry["filled_by"] = source
        entry["filled_at"] = datetime.now(timezone.utc).isoformat()
        save_field_gaps(gaps)


def get_symbol_gaps(symbol: str) -> dict:
    """Return {section: {field: gap_info}} for a symbol. Empty dict if none."""
    return load_field_gaps().get(symbol, {})


def get_unfilled_gaps(symbol: str) -> dict[str, list[str]]:
    """Return {section: [field, ...]} of gaps not yet filled by AI research."""
    all_gaps = get_symbol_gaps(symbol)
    result: dict[str, list[str]] = {}
    for section, fields in all_gaps.items():
        unfilled = [f for f, info in fields.items() if not info.get("filled_by")]
        if unfilled:
            result[section] = unfilled
    return result
