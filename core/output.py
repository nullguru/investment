# -*- coding: utf-8 -*-
"""
CLI output formatting: JSON, table, CSV.
Used by cli.py for consistent output across all subcommands.
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


def _json_safe(v: Any) -> Any:
    """Convert value to JSON-serializable form."""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(v, pd.Timestamp):
        return str(v)
    if hasattr(v, "item"):
        return _json_safe(v.item())
    return v


def _sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _json_safe(v) for k, v in d.items()}


def format_output(
    data: Union[Dict, List, pd.DataFrame],
    fmt: str = "table",
    keys: Optional[List[str]] = None,
) -> str:
    """
    Format data for CLI output.
    - fmt='json': JSON string
    - fmt='table': aligned text table
    - fmt='csv': CSV string
    data can be a dict (single record), list of dicts, or DataFrame.
    keys: optional column subset/ordering.
    """
    # Normalize to list of dicts
    if isinstance(data, pd.DataFrame):
        records = [_sanitize_dict(r) for r in data.to_dict("records")]
    elif isinstance(data, dict):
        records = [_sanitize_dict(data)]
    elif isinstance(data, list):
        records = [_sanitize_dict(r) if isinstance(r, dict) else {"value": r} for r in data]
    else:
        records = [{"value": data}]

    if keys:
        records = [{k: r.get(k) for k in keys} for r in records]

    if fmt == "json":
        return json.dumps({"status": "ok", "count": len(records), "data": records}, indent=2, default=str)

    if fmt == "csv":
        if not records:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        return buf.getvalue()

    # Default: table
    return _format_table(records)


def _format_table(records: List[Dict[str, Any]]) -> str:
    """Render records as an aligned text table."""
    if not records:
        return "(no data)"
    headers = list(records[0].keys())
    # Compute column widths
    widths = {h: len(h) for h in headers}
    str_rows = []
    for r in records:
        row = {}
        for h in headers:
            v = r.get(h)
            s = "" if v is None else str(v)
            if len(s) > 40:
                s = s[:37] + "..."
            row[h] = s
            widths[h] = max(widths[h], len(s))
        str_rows.append(row)

    lines = []
    header_line = "  ".join(h.ljust(widths[h]) for h in headers)
    lines.append(header_line)
    lines.append("  ".join("-" * widths[h] for h in headers))
    for row in str_rows:
        lines.append("  ".join(row[h].ljust(widths[h]) for h in headers))
    return "\n".join(lines)


def print_output(
    data: Union[Dict, List, pd.DataFrame],
    fmt: str = "table",
    keys: Optional[List[str]] = None,
) -> None:
    """Format and print data to stdout."""
    print(format_output(data, fmt=fmt, keys=keys))


def print_error(message: str, fmt: str = "table", needs_web_fetch: Optional[List[str]] = None) -> None:
    """Print error message. In JSON mode, outputs structured error."""
    if fmt == "json":
        err = {"status": "error", "message": message}
        if needs_web_fetch:
            err["needs_web_fetch"] = needs_web_fetch
        print(json.dumps(err, indent=2))
    else:
        print(f"Error: {message}", file=sys.stderr)
        if needs_web_fetch:
            print(f"Missing data requires web fetch: {', '.join(needs_web_fetch)}", file=sys.stderr)
