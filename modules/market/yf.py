# -*- coding: utf-8 -*-
"""
Yahoo Finance service: fetch per-company data by section.
Caches results in memory; force=True bypasses cache.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import yfinance as yf
import pandas as pd
import numpy as np

# In-memory cache: (symbol, section) -> data
_YF_CACHE: Dict[tuple, Dict[str, Any]] = {}


def _ensure_ticker(symbol: str, market: str = "india") -> str:
    """
    Ensure symbol is in the correct format for yfinance.
    - India: bare symbols get .NS suffix (NSE default).
    - US: bare symbols are returned as-is (no suffix needed).
    - If symbol already has a '.', it is returned unchanged.
    """
    s = (symbol or "").strip().upper()
    if not s:
        return symbol
    if "." in s:
        return symbol  # already has exchange suffix
    if market == "us":
        return s  # US tickers are bare (AAPL, MSFT, etc.)
    return s + ".NS"  # India default: NSE


def _safe_val(v: Any) -> Any:
    """Convert to JSON-safe value."""
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    if isinstance(v, (np.integer, np.floating)):
        return float(v) if isinstance(v, np.floating) else int(v)
    if isinstance(v, pd.Timestamp):
        return str(v)
    return v


def _df_to_records(df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of dicts, JSON-safe."""
    if df is None or df.empty:
        return []
    out = []
    for _, row in df.iterrows():
        d = {}
        for k, v in row.items():
            d[str(k)] = _safe_val(v)
        out.append(d)
    return out


def _df_col_to_dict(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Convert DataFrame columns to {col_name: value} for latest period.
    yfinance returns columns in descending order (most recent first)."""
    if df is None or df.empty:
        return {}
    # Use most recent column (first, since columns are descending)
    col = df.columns[0]
    d = {}
    for idx in df.index:
        v = df.loc[idx, col]
        d[str(idx)] = _safe_val(v)
    return d


def _major_holders_to_list(ticker: yf.Ticker) -> List[Dict[str, Any]]:
    """Convert major_holders DataFrame to list of {label, value}."""
    try:
        mh = ticker.major_holders
        if mh is None or mh.empty:
            return []
        out = []
        for idx in mh.index:
            row = mh.loc[idx]
            val = row.iloc[0] if hasattr(row, "iloc") else row.values[0]
            out.append({"label": str(idx), "value": _safe_val(val)})
        return out
    except Exception:
        return []


def _institutional_holders_to_list(ticker: yf.Ticker) -> List[Dict[str, Any]]:
    """Convert institutional_holders to list of {holder, shares, pct, value}."""
    try:
        ih = ticker.institutional_holders
        if ih is None or ih.empty:
            return []
        out = []
        for _, row in ih.head(10).iterrows():
            d = {str(k): _safe_val(v) for k, v in row.items()}
            out.append(d)
        return out
    except Exception:
        return []


def _fetch_overview(ticker: yf.Ticker) -> Dict[str, Any]:
    """Extract overview data from ticker.info."""
    info = ticker.info or {}
    founded = info.get("founded") or info.get("startDate") or info.get("foundationYear")
    if founded and hasattr(founded, "year"):
        founded = str(founded.year)
    held_insiders = info.get("heldPercentInsiders")
    held_inst = info.get("heldPercentInstitutions")
    if held_insiders is not None and isinstance(held_insiders, (int, float)) and held_insiders <= 1:
        held_insiders = held_insiders * 100
    if held_inst is not None and isinstance(held_inst, (int, float)) and held_inst <= 1:
        held_inst = held_inst * 100
    return {
        "longBusinessSummary": info.get("longBusinessSummary") or info.get("longSummary"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "fullTimeEmployees": _safe_val(info.get("fullTimeEmployees")),
        "website": info.get("website"),
        "address1": info.get("address1"),
        "city": info.get("city"),
        "state": info.get("state"),
        "country": info.get("country"),
        "zip": info.get("zip"),
        "fiscalYearEnd": info.get("fiscalYearEnd"),
        "exchange": info.get("exchange"),
        "quoteType": info.get("quoteType"),
        "isin": _get_isin(info),
        "founded": founded,
        "heldPercentInsiders": _safe_val(held_insiders),
        "heldPercentInstitutions": _safe_val(held_inst),
        "majorHolders": _major_holders_to_list(ticker),
        "institutionalHolders": _institutional_holders_to_list(ticker),
        "headquarters": _build_headquarters(info),
    }


def _build_headquarters(info: dict) -> Optional[str]:
    """Build headquarters string from address components."""
    parts = [
        info.get("address1"),
        info.get("city"),
        info.get("state"),
        info.get("country"),
    ]
    parts = [str(p).strip() for p in parts if p]
    return ", ".join(parts) if parts else None


def _get_isin(info: dict) -> Optional[str]:
    """Get ISIN from info."""
    for k in ("isin", "isinCode", "ISIN"):
        if info.get(k):
            return info[k]
    return None


def _fetch_market(ticker: yf.Ticker) -> Dict[str, Any]:
    """Extract market data from ticker."""
    info = ticker.info or {}
    fast = getattr(ticker, "fast_info", None)
    hist = None
    try:
        hist = ticker.history(period="1y")
    except Exception:
        pass

    current_price = None
    high_52w = None
    low_52w = None
    if fast:
        current_price = getattr(fast, "last_price", None) or getattr(fast, "previous_close", None)
    if current_price is None:
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    if hist is not None and not hist.empty:
        high_52w = float(hist["High"].max()) if "High" in hist.columns else None
        low_52w = float(hist["Low"].min()) if "Low" in hist.columns else None
    if high_52w is None:
        high_52w = info.get("fiftyTwoWeekHigh")
    if low_52w is None:
        low_52w = info.get("fiftyTwoWeekLow")

    volume = info.get("volume")
    if volume is None and hist is not None and not hist.empty and "Volume" in hist.columns:
        try:
            volume = float(hist["Volume"].iloc[-1])
        except (IndexError, TypeError):
            pass

    beta = info.get("beta")
    div_yield = info.get("yield") or info.get("dividendYield")
    if div_yield is not None and isinstance(div_yield, float) and div_yield < 1:
        div_yield = div_yield * 100  # convert 0.05 -> 5%

    vs_200dma = None
    if hist is not None and not hist.empty and "Close" in hist.columns:
        close = hist["Close"]
        window = min(200, len(close))
        if window > 0:
            dma = close.rolling(window).mean().iloc[-1]
            last_close = float(close.iloc[-1])
            if dma and dma > 0:
                vs_200dma = round((last_close - dma) / dma * 100, 2)

    return {
        "currentPrice": _safe_val(current_price),
        "fiftyTwoWeekHigh": _safe_val(high_52w),
        "fiftyTwoWeekLow": _safe_val(low_52w),
        "beta": _safe_val(beta),
        "dividendYield": _safe_val(div_yield),
        "volume": _safe_val(volume),
        "averageVolume": _safe_val(info.get("averageVolume")),
        "marketCap": _safe_val(info.get("marketCap")),
        "sharesOutstanding": _safe_val(info.get("sharesOutstanding")),
        "vs200DMA": _safe_val(vs_200dma),
        "payoutRatio": _safe_val(info.get("payoutRatio")),
    }


def _fetch_financials(ticker: yf.Ticker) -> Dict[str, Any]:
    """Extract financial statements and ratios."""
    info = ticker.info or {}
    inc = None
    bal = None
    cf = None
    try:
        inc = ticker.financials
    except Exception:
        pass
    try:
        bal = ticker.balance_sheet
    except Exception:
        pass
    try:
        cf = ticker.cashflow
    except Exception:
        pass

    # Income statement - latest year
    inc_dict = _df_col_to_dict(inc) if inc is not None else {}
    bal_dict = _df_col_to_dict(bal) if bal is not None else {}
    cf_dict = _df_col_to_dict(cf) if cf is not None else {}

    # Derived fields from DataFrames
    total_equity = None
    if bal_dict:
        total_equity = (
            bal_dict.get("Common Stock Equity")
            or bal_dict.get("Stockholders Equity")
            or bal_dict.get("Total Equity Gross Minority Interest")
        )
    total_equity = _safe_val(info.get("totalStockholderEquity") or total_equity)

    total_assets = _safe_val(info.get("totalAssets") or (bal_dict.get("Total Assets") if bal_dict else None))

    net_income = _safe_val(
        info.get("netIncomeToCommon")
        or (inc_dict.get("Net Income") or inc_dict.get("Net Income From Continuing Operations") if inc_dict else None)
    )

    current_ratio = None
    if bal_dict:
        ca = bal_dict.get("Current Assets")
        cl = bal_dict.get("Current Liabilities")
        if ca is not None and cl is not None and float(cl) != 0:
            current_ratio = float(ca) / float(cl)
    if current_ratio is None:
        current_ratio = info.get("currentRatio")

    roe = info.get("returnOnEquity")
    if roe is None and net_income is not None and total_equity and float(total_equity) != 0:
        roe = float(net_income) / float(total_equity)

    roa = info.get("returnOnAssets")
    if roa is None and net_income is not None and total_assets and float(total_assets) != 0:
        roa = float(net_income) / float(total_assets)

    debt_equity = info.get("debtToEquity")
    if debt_equity is not None and isinstance(debt_equity, (int, float)) and debt_equity > 10:
        debt_equity = debt_equity / 100  # yf sometimes returns e.g. 35.6 for 0.356

    return {
        "incomeStatement": inc_dict,
        "incomeStatementHistory": _df_to_records(inc) if inc is not None else [],
        "balanceSheet": bal_dict,
        "balanceSheetHistory": _df_to_records(bal) if bal is not None else [],
        "cashflow": cf_dict,
        "cashflowHistory": _df_to_records(cf) if cf is not None else [],
        "revenue": _safe_val(info.get("totalRevenue") or (inc_dict.get("Total Revenue") if inc_dict else None)),
        "netIncome": net_income,
        "grossMargins": _safe_val(info.get("grossMargins")),
        "operatingMargins": _safe_val(info.get("operatingMargins")),
        "profitMargins": _safe_val(info.get("profitMargins")),
        "ebitda": _safe_val(info.get("ebitda")),
        "ebitdaMargins": _safe_val(info.get("ebitdaMargins")),
        "totalDebt": _safe_val(info.get("totalDebt") or (bal_dict.get("Total Debt") if bal_dict else None)),
        "totalCash": _safe_val(
            info.get("totalCash")
            or (bal_dict.get("Cash And Cash Equivalents") or bal_dict.get("Cash Cash Equivalents And Short Term Investments") if bal_dict else None)
        ),
        "totalAssets": total_assets,
        "totalEquity": total_equity,
        "operatingCashFlow": _safe_val(cf_dict.get("Operating Cash Flow") if cf_dict else None),
        "freeCashFlow": _safe_val(
            info.get("freeCashflow")
            or (cf_dict.get("Free Cash Flow") if cf_dict else None)
        ),
        "capitalExpenditure": _safe_val(
            cf_dict.get("Capital Expenditure") or cf_dict.get("Capital Expenditure Reported") if cf_dict else None
        ),
        "returnOnEquity": _safe_val(roe),
        "returnOnAssets": _safe_val(roa),
        "returnOnCapital": _safe_val(info.get("returnOnCapital")),
        "currentRatio": _safe_val(current_ratio),
        "quickRatio": _safe_val(info.get("quickRatio")),
        "debtToEquity": _safe_val(debt_equity),
        "workingCapital": _safe_val(bal_dict.get("Working Capital") if bal_dict else None),
        "effectiveTaxRate": _safe_val(info.get("effectiveTaxRate") or (inc_dict.get("Tax Rate For Calcs") if inc_dict else None)),
        "financialCurrency": info.get("financialCurrency") or info.get("currency"),
    }


def _fetch_valuation(ticker: yf.Ticker) -> Dict[str, Any]:
    """Extract valuation multiples."""
    info = ticker.info or {}
    pe = info.get("trailingPE") or info.get("forwardPE")
    fwd_pe = info.get("forwardPE")
    peg = info.get("pegRatio")
    pb = info.get("priceToBook")
    ev_ebitda = info.get("enterpriseToEbitda")
    ev_rev = info.get("enterpriseToRevenue")
    earnings_yield = (1 / pe * 100) if pe and pe > 0 else None
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    price_to_sales = info.get("priceToSalesTrailing12Months")

    pfcf = None
    fcf = info.get("freeCashflow")
    if fcf is None:
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                fcf = cf.loc["Free Cash Flow", cf.columns[-1]] if "Free Cash Flow" in cf.index else None
        except Exception:
            pass
    shares = info.get("sharesOutstanding")
    if fcf is not None and shares and current_price and shares > 0 and fcf > 0:
        fcf_per_share = float(fcf) / float(shares)
        pfcf = float(current_price) / fcf_per_share

    return {
        "trailingPE": _safe_val(pe),
        "forwardPE": _safe_val(fwd_pe),
        "pegRatio": _safe_val(peg),
        "priceToBook": _safe_val(pb),
        "enterpriseToEbitda": _safe_val(ev_ebitda),
        "enterpriseToRevenue": _safe_val(ev_rev),
        "earningsYield": _safe_val(earnings_yield),
        "currentPrice": _safe_val(current_price),
        "targetMeanPrice": _safe_val(target_mean),
        "targetHighPrice": _safe_val(target_high),
        "targetLowPrice": _safe_val(target_low),
        "marketCap": _safe_val(info.get("marketCap")),
        "enterpriseValue": _safe_val(info.get("enterpriseValue")),
        "dividendYield": _safe_val(info.get("yield") or info.get("dividendYield")),
        "payoutRatio": _safe_val(info.get("payoutRatio")),
        "priceToSalesTrailing12Months": _safe_val(price_to_sales),
        "priceToSales": _safe_val(price_to_sales),
        "priceToFreeCashFlow": _safe_val(pfcf),
    }


def get_section_data(symbol: str, section: str, force: bool = False, market: str = "india") -> Dict[str, Any]:
    """
    Fetch yfinance data for a symbol and section.
    Sections: overview, market, financials, valuation.
    Results are cached unless force=True.
    market: 'india' (default) or 'us' — controls ticker suffix handling.
    """
    ticker_str = _ensure_ticker(symbol, market)
    cache_key = (ticker_str, section)

    if not force and cache_key in _YF_CACHE:
        return _YF_CACHE[cache_key].copy()

    try:
        ticker = yf.Ticker(ticker_str)
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

    fetchers = {
        "overview": _fetch_overview,
        "market": _fetch_market,
        "financials": _fetch_financials,
        "valuation": _fetch_valuation,
    }

    if section not in fetchers:
        return {"error": f"Unknown section: {section}", "symbol": symbol}

    try:
        data = fetchers[section](ticker)
        data["symbol"] = symbol
        data["_ticker"] = ticker_str
        _YF_CACHE[cache_key] = data.copy()
        return data
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_price_history(symbol: str, market: str = "india") -> Dict[str, Any]:
    """Return 2-year daily price + volume history with 50/200 DMA for charting."""
    ticker_str = _ensure_ticker(symbol, market)
    cache_key = (ticker_str, "price_history")
    if cache_key in _YF_CACHE:
        return _YF_CACHE[cache_key].copy()

    try:
        ticker = yf.Ticker(ticker_str)
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

    try:
        hist = ticker.history(period="2y", interval="1d")
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

    if hist is None or hist.empty:
        return {"error": "No price data available", "symbol": symbol}

    close = hist["Close"]
    volume = hist["Volume"] if "Volume" in hist.columns else pd.Series(dtype=float)

    ma50  = close.rolling(50,  min_periods=1).mean()
    ma200 = close.rolling(200, min_periods=1).mean()

    def _fmt_date(ts) -> str:
        try:
            return ts.strftime("%Y-%m-%d")
        except Exception:
            return str(ts)[:10]

    dates   = [_fmt_date(t) for t in hist.index]
    prices  = [_safe_val(v) for v in close]
    vol     = [_safe_val(v) for v in volume] if not volume.empty else [None] * len(dates)
    sma50   = [round(float(v), 2) if not (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else None for v in ma50]
    sma200  = [round(float(v), 2) if not (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else None for v in ma200]

    # Current vs DMA summary — use last non-None value
    last_price  = next((v for v in reversed(prices)  if v is not None), None)
    last_sma50  = next((v for v in reversed(sma50)   if v is not None), None)
    last_sma200 = next((v for v in reversed(sma200)  if v is not None), None)

    vs50  = round((last_price / last_sma50  - 1) * 100, 2) if last_price and last_sma50  and last_sma50  != 0 else None
    vs200 = round((last_price / last_sma200 - 1) * 100, 2) if last_price and last_sma200 and last_sma200 != 0 else None

    result = {
        "symbol": symbol,
        "dates":  dates,
        "price":  prices,
        "sma50":  sma50,
        "sma200": sma200,
        "volume": vol,
        "summary": {
            "last_price": last_price,
            "sma50": last_sma50,
            "sma200": last_sma200,
            "vs_sma50_pct": vs50,
            "vs_sma200_pct": vs200,
        },
    }
    _YF_CACHE[cache_key] = result.copy()
    return result


def get_metrics_history(symbol: str, market: str = "india") -> Dict[str, Any]:
    """Return multi-year timeseries of financial metrics for chart rendering."""
    ticker_str = _ensure_ticker(symbol, market)
    cache_key = (ticker_str, "metrics_history")
    if cache_key in _YF_CACHE:
        return _YF_CACHE[cache_key].copy()

    try:
        ticker = yf.Ticker(ticker_str)
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

    inc = bal = cf = None
    try:
        inc = ticker.financials
    except Exception:
        pass
    try:
        bal = ticker.balance_sheet
    except Exception:
        pass
    try:
        cf = ticker.cashflow
    except Exception:
        pass

    if inc is None or inc.empty:
        return {"error": "No financial data available", "symbol": symbol}

    def _row(df, *keys) -> Dict[str, Any]:
        if df is None:
            return {}
        for k in keys:
            if k in df.index:
                return {str(c)[:4]: _safe_val(df.loc[k, c]) for c in df.columns}
        return {}

    revenue      = _row(inc, "Total Revenue")
    gross_profit = _row(inc, "Gross Profit")
    op_income    = _row(inc, "Operating Income", "EBIT")
    net_income   = _row(inc, "Net Income", "Net Income From Continuing Operations")
    ebitda_row   = _row(inc, "EBITDA", "Normalized EBITDA")
    interest_exp = _row(inc, "Interest Expense", "Interest Expense Non Operating")
    rd_exp       = _row(inc, "Research And Development", "Research Development")
    tax_rate_row = _row(inc, "Tax Rate For Calcs")

    total_equity = _row(bal, "Common Stock Equity", "Stockholders Equity", "Total Equity Gross Minority Interest")
    total_assets = _row(bal, "Total Assets")
    total_debt   = _row(bal, "Total Debt", "Long Term Debt And Capital Lease Obligation")
    cash_row     = _row(bal, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
    shares_row   = _row(bal, "Share Issued", "Ordinary Shares Number")

    fcf_row   = _row(cf, "Free Cash Flow")
    capex_row = _row(cf, "Capital Expenditure", "Capital Expenditure Reported")

    years = sorted({y for d in [revenue, gross_profit, op_income, net_income] for y in d})

    result_years = []
    rev_series = []
    ni_series = []
    gross_margins = []
    op_margins = []
    net_margins = []
    roe_series = []
    roa_series = []
    roic_series = []
    fcf_conversion = []
    capex_rev = []
    rd_rev = []
    de_ratio = []
    net_debt_ebitda = []
    int_coverage = []
    pe_hist = []
    pb_hist = []
    ps_hist = []

    for y in years:
        rev = revenue.get(y)
        gp  = gross_profit.get(y)
        op  = op_income.get(y)
        ni  = net_income.get(y)
        eb  = ebitda_row.get(y)
        ie  = interest_exp.get(y)
        rd  = rd_exp.get(y)
        tr  = tax_rate_row.get(y)
        te  = total_equity.get(y)
        ta  = total_assets.get(y)
        td  = total_debt.get(y)
        c   = cash_row.get(y)
        sh  = shares_row.get(y)
        f   = fcf_row.get(y)
        cx  = capex_row.get(y)

        result_years.append(y)
        rev_series.append(rev)
        ni_series.append(ni)

        def _pct(a, b):
            try:
                return round(a / b * 100, 1) if a and b and float(b) != 0 else None
            except Exception:
                return None

        gross_margins.append(_pct(gp, rev))
        op_margins.append(_pct(op, rev))
        net_margins.append(_pct(ni, rev))
        roe_series.append(_pct(ni, te))
        roa_series.append(_pct(ni, ta))

        roic = None
        try:
            if op and te is not None and td is not None and c is not None:
                tax = float(tr) if tr and 0 < float(tr) < 1 else 0.25
                nopat = float(op) * (1 - tax)
                ic = float(te) + float(td) - float(c)
                roic = round(nopat / ic * 100, 1) if ic != 0 else None
        except Exception:
            pass
        roic_series.append(roic)

        fcf_conversion.append(_pct(f, ni))
        capex_rev.append(round(abs(float(cx)) / float(rev) * 100, 1) if cx and rev and float(rev) != 0 else None)
        rd_rev.append(_pct(rd, rev))

        de_ratio.append(round(float(td) / float(te), 2) if td and te and float(te) != 0 else None)

        try:
            nd = float(td or 0) - float(c or 0) if td is not None else None
            net_debt_ebitda.append(round(nd / float(eb), 2) if nd is not None and eb and float(eb) != 0 else None)
        except Exception:
            net_debt_ebitda.append(None)

        try:
            int_coverage.append(round(abs(float(op) / float(ie)), 1) if op and ie and float(ie) != 0 else None)
        except Exception:
            int_coverage.append(None)

        pe_hist.append(None)
        pb_hist.append(None)
        ps_hist.append(None)

    # Historical valuation: year-end price × per-share denominators
    try:
        price_hist = ticker.history(period="5y", interval="1mo")
        if not price_hist.empty:
            for i, y in enumerate(result_years):
                yp = price_hist[price_hist.index.year == int(y)]
                if yp.empty:
                    continue
                px = float(yp["Close"].iloc[-1])
                sh = shares_row.get(y)
                ni = ni_series[i]
                rev = rev_series[i]
                te = total_equity.get(y)
                if sh and float(sh) > 0:
                    if ni:
                        eps = float(ni) / float(sh)
                        pe_hist[i] = round(px / eps, 1) if eps > 0 else None
                    if te:
                        bvps = float(te) / float(sh)
                        pb_hist[i] = round(px / bvps, 2) if bvps > 0 else None
                    if rev:
                        sps = float(rev) / float(sh)
                        ps_hist[i] = round(px / sps, 2) if sps > 0 else None
    except Exception:
        pass

    result = {
        "symbol": symbol,
        "years": result_years,
        "revenue": [_safe_val(v) for v in rev_series],
        "net_income": [_safe_val(v) for v in ni_series],
        "margins": {"gross": gross_margins, "operating": op_margins, "net": net_margins},
        "returns": {"roe": roe_series, "roa": roa_series, "roic": roic_series},
        "cash_quality": {"fcf_conversion": fcf_conversion, "capex_to_revenue": capex_rev, "rd_to_revenue": rd_rev},
        "leverage": {"debt_to_equity": de_ratio, "net_debt_to_ebitda": net_debt_ebitda, "interest_coverage": int_coverage},
        "valuation_history": {"pe": pe_hist, "pb": pb_hist, "ps": ps_hist},
    }
    _YF_CACHE[cache_key] = result.copy()
    return result


def clear_cache(symbol: Optional[str] = None, section: Optional[str] = None) -> int:
    """Clear cache. If symbol/section given, clear only those. Returns count cleared."""
    if symbol is None and section is None:
        n = len(_YF_CACHE)
        _YF_CACHE.clear()
        return n
    to_del = [
        k for k in _YF_CACHE
        if (symbol is None or k[0] == symbol or k[0] == _ensure_ticker(symbol, "india") or k[0] == _ensure_ticker(symbol, "us"))
        and (section is None or k[1] == section)
    ]
    for k in to_del:
        del _YF_CACHE[k]
    return len(to_del)
