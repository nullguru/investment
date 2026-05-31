# -*- coding: utf-8 -*-
"""
Sharia compliance filter: fetches total assets, cash, receivables, revenue metrics,
debt-to-equity, and computes strict Sharia rules (all must pass).

Fetches: annual for preceding years (2021–2025) and annual up to 31 Mar 2026;
quarterly from 2026 (Jun/Sep/Dec 2026) up to the last completed quarter as of today.
Financial year end (e.g. 31 Mar) is kept as annual only; reruns pick up new quarters when available.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, List, Optional, Tuple
import time

import pandas as pd
import yfinance as yf

# Strict thresholds (decimals)
CASH_TO_ASSETS_MAX = 0.33   # Cash And Short Term Investments / Total Assets < 33%
OTHER_REVENUE_TO_REVENUE_MAX = 0.05  # Other Revenue / Total Revenue < 5%
RECEIVABLES_TO_ASSETS_MAX = 0.50     # Total Receivables / Total Assets < 50%
DEBT_TO_EQUITY_MAX = 0.33           # Debt to equity ratio < 33%

# Industries/sectors not allowed for Sharia (core business). Match by substring (case-insensitive).
NON_COMPLIANT_INDUSTRY_KEYWORDS = [
    "bank", "banking", "credit service", "mortgage", "insurance", "financial services",
    "alcohol", "brewer", "winery", "distill", "liquor", "spirits",
    "gambling", "casino", "lottery", "betting",
    "pork", "pig ",
    "adult entertainment", "adult content",
    "tobacco", "cigarette", "cigar",
    "weapon", "armament", "defense", "military", "aerospace & defense",
]

# Annual: preceding years 2021–2025 and 2026 up to FY end
# India FY: Apr–Mar (ends 31 Mar), US FY: Jan–Dec (ends 31 Dec, most companies)
ANNUAL_START = date(2021, 1, 1)
ANNUAL_END = date(2026, 3, 31)          # India default

# Quarterly: from first quarter after FY end 2026 through last completed quarter (computed at run time)
QUARTERLY_START = date(2026, 4, 1)      # India default (excludes 31 Mar so it stays annual only)

# Per-market date configuration
MARKET_DATE_CONFIG: dict = {
    "india": {
        "annual_start": date(2021, 1, 1),
        "annual_end": date(2026, 3, 31),
        "quarterly_start": date(2026, 4, 1),
    },
    "us": {
        "annual_start": date(2021, 1, 1),
        "annual_end": date(2025, 12, 31),
        "quarterly_start": date(2026, 1, 1),
    },
}


def _last_quarter_end(as_of: date) -> date:
    """Return the latest standard quarter-end date that is <= as_of (Mar 31, Jun 30, Sep 30, Dec 31)."""
    for month, day in [(12, 31), (9, 30), (6, 30), (3, 31)]:
        q = date(as_of.year, month, day)
        if q <= as_of:
            return q
    return date(as_of.year - 1, 12, 31)


def _is_industry_sharia_excluded(industry: Optional[str], sector: Optional[str]) -> bool:
    """True if industry or sector matches a non-compliant business (banking, alcohol, gambling, etc.)."""
    text = " ".join(filter(None, [industry or "", sector or ""])).lower()
    if not text:
        return False
    return any(kw in text for kw in NON_COMPLIANT_INDUSTRY_KEYWORDS)


def is_industry_compliant(industry: Optional[str], sector: Optional[str]) -> bool:
    """True if industry/sector is allowed for Sharia (not in non-allowed list)."""
    return not _is_industry_sharia_excluded(industry, sector)


class ShariaStatus(str, Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "Unknown"


def _safe_float(val: Any) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _get_row_value(df, index_names, default=0.0):
    """Get first period value (iloc[0] = most recent reported period from yfinance)."""
    if df is None or df.empty:
        return default
    for name in index_names:
        if name in df.index:
            row = df.loc[name]
            val = row.iloc[0] if hasattr(row, "iloc") else row
            return _safe_float(val)
    return default


def _get_row_value_for_column(df: Optional[pd.DataFrame], col_index: int, index_names: List[str], default: Any = 0.0) -> Any:
    """Get value for a specific column (period). Returns default if row/column missing."""
    if df is None or df.empty or col_index >= len(df.columns):
        return default
    for name in index_names:
        if name in df.index:
            row = df.loc[name]
            if hasattr(row, "iloc"):
                val = row.iloc[col_index]
            else:
                val = default
            return _safe_float(val) if val is not None and not (isinstance(val, float) and pd.isna(val)) else default
    return default


def _column_dates_in_range(df: Optional[pd.DataFrame], start: date, end: date) -> List[Tuple[int, date, str]]:
    """Return list of (column_index, period_date, period_str) for columns within [start, end] inclusive."""
    if df is None or df.empty or len(df.columns) == 0:
        return []
    out = []
    for i, col in enumerate(df.columns):
        try:
            ts = pd.Timestamp(col)
            d = ts.date() if hasattr(ts, "date") else ts.to_pydatetime().date()
            if start <= d <= end:
                out.append((i, d, str(d)))
        except Exception:
            continue
    return out


def _get_report_period(balance_sheet) -> Optional[str]:
    """Return the date of the most recent period (first column) as string, or None."""
    if balance_sheet is None or balance_sheet.empty or len(balance_sheet.columns) == 0:
        return None
    try:
        col = balance_sheet.columns[0]
        return str(pd.Timestamp(col).date()) if col is not None else None
    except Exception:
        return None


def _compute_metrics_for_period(
    symbol: str,
    balance_sheet: Optional[pd.DataFrame],
    income_stmt: Optional[pd.DataFrame],
    col_index: int,
    report_period_str: str,
    period_type: str,
    name: Optional[str],
    industry: Optional[str],
    sector: Optional[str],
    market_cap: Optional[float],
    info: dict,
) -> Optional[ShariaMetrics]:
    """Compute Sharia metrics for one period (one column)."""
    total_assets = _get_row_value_for_column(
        balance_sheet, col_index,
        ["Total Assets", "Total assets"],
        None,
    )
    if total_assets is None or total_assets == 0:
        return None

    cash_and_short_term = _get_row_value_for_column(
        balance_sheet, col_index,
        [
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Cash Equivalents",
            "Cash and Cash Equivalents",
        ],
        None,
    )
    if cash_and_short_term is None:
        cash_and_short_term = _safe_float(info.get("totalCash")) or _safe_float(info.get("totalCashEquivalents"))

    total_receivables = _get_row_value_for_column(
        balance_sheet, col_index,
        ["Net Receivables", "Accounts Receivable", "Receivables"],
        None,
    )

    total_revenue = _get_row_value_for_column(
        income_stmt, col_index,
        ["Total Revenue", "Operating Revenue", "Revenue", "Revenues"],
        None,
    )
    other_revenue = _get_row_value_for_column(
        income_stmt, col_index,
        ["Other Revenue", "Other Operating Income", "Non Operating Income", "Other Income"],
        0.0,
    )

    total_equity = _get_row_value_for_column(
        balance_sheet, col_index,
        ["Total Stockholder Equity", "Total Equity Gross Minority Interest", "Stockholders Equity"],
        None,
    )
    total_debt_bs = _get_row_value_for_column(
        balance_sheet, col_index,
        ["Total Debt", "Net Debt"],
        None,
    )
    total_debt = total_debt_bs if total_debt_bs is not None else _safe_float(info.get("totalDebt")) or None
    if total_debt is not None and total_equity is not None and total_equity > 0:
        debt_to_equity = total_debt / total_equity
    else:
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is None and total_debt is not None and total_equity is not None and total_equity > 0:
            debt_to_equity = total_debt / total_equity

    cash_to_assets_pct = 0.0
    other_revenue_to_revenue_pct = 0.0
    receivables_to_assets_pct = 0.0
    if total_assets and total_assets > 0:
        if cash_and_short_term is not None:
            cash_to_assets_pct = round((cash_and_short_term / total_assets) * 100, 2)
        if total_receivables is not None:
            receivables_to_assets_pct = round((total_receivables / total_assets) * 100, 2)
    if total_revenue and total_revenue > 0 and other_revenue is not None:
        other_revenue_to_revenue_pct = round((other_revenue / total_revenue) * 100, 2)

    ok_debt = debt_to_equity is not None and _safe_float(debt_to_equity) < DEBT_TO_EQUITY_MAX
    ok_cash = total_assets and total_assets > 0 and cash_and_short_term is not None and (cash_and_short_term / total_assets) < CASH_TO_ASSETS_MAX
    ok_other_rev = total_revenue and total_revenue > 0 and other_revenue is not None and (other_revenue / total_revenue) < OTHER_REVENUE_TO_REVENUE_MAX
    ok_receivables = total_assets and total_assets > 0 and total_receivables is not None and (total_receivables / total_assets) < RECEIVABLES_TO_ASSETS_MAX

    if ok_debt and ok_cash and ok_other_rev and ok_receivables:
        compliant = ShariaStatus.YES
    elif (
        (debt_to_equity is not None or (total_assets and cash_and_short_term is not None))
        and (total_revenue is not None or (total_assets and total_receivables is not None))
    ):
        compliant = ShariaStatus.NO
    else:
        compliant = ShariaStatus.UNKNOWN

    industry_compliant = is_industry_compliant(industry, sector)
    if _is_industry_sharia_excluded(industry, sector):
        compliant = ShariaStatus.NO

    return ShariaMetrics(
        symbol=symbol,
        name=name or symbol,
        total_assets=total_assets,
        cash_and_short_term_investments=cash_and_short_term,
        total_receivables=total_receivables,
        other_revenue=other_revenue,
        total_revenue=total_revenue,
        debt_to_equity_ratio=_safe_float(debt_to_equity) if debt_to_equity is not None else None,
        cash_to_assets_pct=cash_to_assets_pct,
        other_revenue_to_revenue_pct=other_revenue_to_revenue_pct,
        receivables_to_assets_pct=receivables_to_assets_pct,
        compliant=compliant,
        report_period=report_period_str,
        period_type=period_type,
        industry=industry,
        sector=sector,
        market_cap=market_cap,
        industry_compliant=industry_compliant,
    )


@dataclass
class ShariaMetrics:
    symbol: str
    name: Optional[str]
    total_assets: Optional[float]
    cash_and_short_term_investments: Optional[float]
    total_receivables: Optional[float]
    other_revenue: Optional[float]
    total_revenue: Optional[float]
    debt_to_equity_ratio: Optional[float]
    cash_to_assets_pct: float
    other_revenue_to_revenue_pct: float
    receivables_to_assets_pct: float
    compliant: ShariaStatus
    report_period: Optional[str] = None
    period_type: str = "annual"  # "annual" | "quarterly"
    industry: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    industry_compliant: bool = True


def _fetch_sharia_metrics_once(symbol: str, market: str = "india") -> List[ShariaMetrics]:
    """
    Fetch yfinance data and compute Sharia metrics for all target periods:
    - Annual: report dates 2021 through market FY end.
    - Quarterly: from first quarter after FY end through last completed quarter as of today.
    market: 'india' (default, FY ends Mar 31) or 'us' (FY ends Dec 31 for most companies).
    """
    cfg = MARKET_DATE_CONFIG.get(market, MARKET_DATE_CONFIG["india"])
    _annual_start = cfg["annual_start"]
    _annual_end = cfg["annual_end"]
    _quarterly_start = cfg["quarterly_start"]

    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    name = info.get("longName") or info.get("shortName") or symbol
    industry = info.get("industry")
    sector = info.get("sector")
    market_cap = info.get("marketCap")

    balance_sheet = getattr(ticker, "balance_sheet", None)
    _inc = getattr(ticker, "income_stmt", None)
    income_stmt = _inc if _inc is not None else getattr(ticker, "financials", None)
    q_balance_sheet = getattr(ticker, "quarterly_balance_sheet", None)
    q_income_stmt = getattr(ticker, "quarterly_income_stmt", None)
    if q_income_stmt is None:
        q_income_stmt = getattr(ticker, "quarterly_financials", None)

    results: List[ShariaMetrics] = []

    # Annual: 2021 through market FY end
    for col_index, _d, report_period_str in _column_dates_in_range(balance_sheet, _annual_start, _annual_end):
        try:
            m = _compute_metrics_for_period(
                symbol=symbol,
                balance_sheet=balance_sheet,
                income_stmt=income_stmt,
                col_index=col_index,
                report_period_str=report_period_str,
                period_type="annual",
                name=name,
                industry=industry,
                sector=sector,
                market_cap=market_cap,
                info=info,
            )
            if m is not None:
                results.append(m)
        except Exception:
            continue

    # Quarterly: from first quarter after FY end through last completed quarter
    quarterly_end = _last_quarter_end(date.today())
    existing_report_periods = {m.report_period for m in results if m.report_period}
    for col_index, _d, report_period_str in _column_dates_in_range(q_balance_sheet, _quarterly_start, quarterly_end):
        if report_period_str in existing_report_periods:
            continue
        try:
            m = _compute_metrics_for_period(
                symbol=symbol,
                balance_sheet=q_balance_sheet,
                income_stmt=q_income_stmt,
                col_index=col_index,
                report_period_str=report_period_str,
                period_type="quarterly",
                name=name,
                industry=industry,
                sector=sector,
                market_cap=market_cap,
                info=info,
            )
            if m is not None:
                results.append(m)
        except Exception:
            continue

    # If no period had enough data, return one UNKNOWN row so symbol still appears
    if not results:
        results.append(ShariaMetrics(
            symbol=symbol,
            name=name,
            total_assets=None,
            cash_and_short_term_investments=None,
            total_receivables=None,
            other_revenue=None,
            total_revenue=None,
            debt_to_equity_ratio=None,
            cash_to_assets_pct=0.0,
            other_revenue_to_revenue_pct=0.0,
            receivables_to_assets_pct=0.0,
            compliant=ShariaStatus.UNKNOWN,
            report_period=None,
            period_type="annual",
            industry=industry,
            sector=sector,
            market_cap=market_cap,
            industry_compliant=is_industry_compliant(industry, sector),
        ))

    return results


# Retry delay for 401 Invalid Crumb (seconds)
_CRUMB_RETRY_DELAY = 2.5
_CRUMB_RETRY_MAX = 2


def get_sharia_metrics(symbol: str, market: str = "india") -> List[ShariaMetrics]:
    """
    Fetch yfinance data and compute Sharia metrics.
    Retries on 401 Invalid Crumb. Returns list of metrics (one per period).
    market: 'india' (default) or 'us' — affects fiscal year date range.
    """
    last_err = None
    for attempt in range(_CRUMB_RETRY_MAX + 1):
        try:
            return _fetch_sharia_metrics_once(symbol, market=market)
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if attempt < _CRUMB_RETRY_MAX and ("401" in err_str or "invalid crumb" in err_str or "unauthorized" in err_str):
                time.sleep(_CRUMB_RETRY_DELAY)
                continue
            break

    # Best-effort: salvage ticker.info metadata even when financials fetch failed.
    # Without this, industry/sector/market_cap are lost and the cached stub is useless.
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        info = {}
    return [
        ShariaMetrics(
            symbol=symbol,
            name=info.get("longName") or info.get("shortName") or symbol,
            total_assets=None,
            cash_and_short_term_investments=None,
            total_receivables=None,
            other_revenue=None,
            total_revenue=None,
            debt_to_equity_ratio=None,
            cash_to_assets_pct=0.0,
            other_revenue_to_revenue_pct=0.0,
            receivables_to_assets_pct=0.0,
            compliant=ShariaStatus.UNKNOWN,
            report_period=None,
            period_type="annual",
            industry=info.get("industry"),
            sector=info.get("sector"),
            market_cap=info.get("marketCap"),
            industry_compliant=is_industry_compliant(info.get("industry"), info.get("sector")),
        )
    ]


def get_sharia_metrics_batch(symbols: List[str], market: str = "india") -> List[ShariaMetrics]:
    """Get Sharia metrics for multiple symbols (sequential)."""
    out: List[ShariaMetrics] = []
    for s in symbols:
        out.extend(get_sharia_metrics(s, market=market))
    return out


def get_sharia_metrics_batch_parallel(
    symbols: List[str],
    max_workers: int = 5,
    delay_between_batches: float = 0.5,
    market: str = "india",
) -> List[ShariaMetrics]:
    """Get Sharia metrics in parallel. Throttles to reduce Yahoo 401 errors."""
    results: List[ShariaMetrics] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {}
        for i, s in enumerate(symbols):
            future_to_sym[executor.submit(get_sharia_metrics, s, market)] = s
            if (i + 1) % 3 == 0 and delay_between_batches > 0:
                time.sleep(delay_between_batches)
        for future in as_completed(future_to_sym):
            try:
                results.extend(future.result())
            except Exception:
                sym = future_to_sym[future]
                results.extend(get_sharia_metrics(sym, market=market))
    return results


def sharia_metrics_to_dataframe(metrics: List[ShariaMetrics]) -> pd.DataFrame:
    """Convert to DataFrame for UI/export (includes period_type)."""
    rows = []
    for m in metrics:
        rows.append({
            "symbol": m.symbol,
            "name": m.name or m.symbol,
            "total_assets": m.total_assets,
            "cash_and_short_term_investments": m.cash_and_short_term_investments,
            "total_receivables": m.total_receivables,
            "other_revenue": m.other_revenue,
            "total_revenue": m.total_revenue,
            "debt_to_equity_ratio": m.debt_to_equity_ratio,
            "cash_to_assets_pct": m.cash_to_assets_pct,
            "other_revenue_to_revenue_pct": m.other_revenue_to_revenue_pct,
            "receivables_to_assets_pct": m.receivables_to_assets_pct,
            "compliant": m.compliant.value,
            "report_period": m.report_period,
            "period_type": getattr(m, "period_type", "annual"),
            "industry": m.industry,
            "sector": m.sector,
            "market_cap": m.market_cap,
            "industry_compliant": getattr(m, "industry_compliant", True),
        })
    return pd.DataFrame(rows)
