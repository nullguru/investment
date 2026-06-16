# -*- coding: utf-8 -*-
"""
Mutual Fund holdings importer.

Reads Groww/broker MF Excel exports (Mutual_Funds_*.xlsx) and stores them
as a snapshot in db/mf_holdings.json.

Excel format (0-indexed rows):
  Row 12-13: Summary (Total Investments, Current Portfolio Value, P/L, XIRR)
  Row 20: Column headers
  Row 22+: Holdings data
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from core.config import DB_DIR

DEFAULT_XLSX_PATH = Path("raw_data/Mutual_Funds_1693120989_15-06-2026_15-06-2026.xlsx")
MF_HOLDINGS_PATH = DB_DIR / "mf_holdings.json"


def _load_stored() -> dict:
    import json
    if MF_HOLDINGS_PATH.exists():
        return json.loads(MF_HOLDINGS_PATH.read_text())
    return {}


def _save(data: dict) -> None:
    import json
    MF_HOLDINGS_PATH.write_text(json.dumps(data, indent=2, default=str))


def _parse_pct(val) -> float:
    """Convert '‑7.23%' or -0.0723 → float percent like -7.23."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    s = str(val).strip().replace("‑", "-").replace("−", "-")
    if s.endswith("%"):
        try:
            return float(s[:-1])
        except ValueError:
            return 0.0
    try:
        v = float(s)
        # If stored as decimal (e.g. -0.0723) convert to percentage
        if abs(v) < 1.5:
            return round(v * 100, 4)
        return round(v, 4)
    except ValueError:
        return 0.0


def import_from_xlsx(path: Path | None = None) -> dict:
    """
    Parse MF holdings Excel and persist to db/mf_holdings.json.

    Returns:
        {"holdings": int, "as_of_date": str, "error": str|None}
    """
    if path is None:
        path = DEFAULT_XLSX_PATH
    path = Path(path)
    if not path.exists():
        return {"holdings": 0, "as_of_date": "", "error": f"File not found: {path}"}

    try:
        raw = pd.read_excel(path, header=None, engine="openpyxl")
    except Exception as exc:
        return {"holdings": 0, "as_of_date": "", "error": f"Failed to read Excel: {exc}"}

    # ── Summary row (row index 13) ────────────────────────────────────────────
    summary_row = raw.iloc[13] if len(raw) > 13 else pd.Series([None] * 11)
    summary = {
        "total_invested":   _safe_float(summary_row.iloc[0]),
        "current_value":    _safe_float(summary_row.iloc[1]),
        "profit_loss":      _safe_float(summary_row.iloc[2]),
        "profit_loss_pct":  _parse_pct(summary_row.iloc[3]),
        "xirr_pct":         _parse_pct(summary_row.iloc[4]),
    }

    # ── As-of date from row 17 ────────────────────────────────────────────────
    as_of_date = ""
    if len(raw) > 17:
        cell = str(raw.iloc[17, 0]).strip()
        # "HOLDINGS AS ON 2026-06-15"
        for part in cell.split():
            if len(part) == 10 and part[4] == "-":
                as_of_date = part
                break

    # ── Holdings (header at row 20, data from row 22) ────────────────────────
    if len(raw) <= 22:
        return {"holdings": 0, "as_of_date": as_of_date, "error": "No holdings rows found"}

    header_row = raw.iloc[20]
    data = raw.iloc[22:].copy()
    data.columns = range(len(data.columns))

    holdings = []
    for _, row in data.iterrows():
        scheme = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        if not scheme or scheme.lower() == "nan":
            continue
        holdings.append({
            "scheme_name":     scheme,
            "amc":             str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else "",
            "category":        str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "",
            "sub_category":    str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "",
            "folio_no":        str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "",
            "source":          str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "",
            "units":           _safe_float(row.iloc[6]),
            "invested_value":  _safe_float(row.iloc[7]),
            "current_value":   _safe_float(row.iloc[8]),
            "returns":         _safe_float(row.iloc[9]),
            "xirr_pct":        _parse_pct(row.iloc[10]),
        })

    data_out = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "as_of_date":  as_of_date,
        "summary":     summary,
        "holdings":    holdings,
    }
    _save(data_out)
    return {"holdings": len(holdings), "as_of_date": as_of_date, "error": None}


def get_holdings() -> dict:
    """Return stored MF holdings, importing from default file if not yet stored."""
    stored = _load_stored()
    if stored:
        return stored
    # Auto-import from default path if it exists
    if DEFAULT_XLSX_PATH.exists():
        import_from_xlsx()
        return _load_stored()
    return {}


def _safe_float(val) -> float:
    try:
        v = float(val)
        return round(v, 4) if not pd.isna(v) else 0.0
    except Exception:
        return 0.0
