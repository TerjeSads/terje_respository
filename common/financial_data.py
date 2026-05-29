from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
import yfinance as yf

INSTRUMENT_TICKERS = {
    "Telenor ASA": "TEL.OL",
    "Apple": "AAPL",
    "Meta": "META",
    "S&P 500": "^GSPC",
    "Nikkei 225 (Japan)": "^N225",
    "STOXX Europe 600": "^STOXX",
    "MSCI World (ETF)": "URTH",
}

RATE_SERIES_OPTIONS = [
    "US 5Y Treasury yield",
    "US 10Y Treasury yield",
    "US 30Y Treasury yield",
]

US_TREASURY_TICKERS = {
    "US 5Y Treasury yield": ("^FVX",),
    "US 10Y Treasury yield": ("^TNX",),
    "US 30Y Treasury yield": ("^TYX",),
}


def _to_date_str(start_date: date) -> str:
    return pd.Timestamp(start_date).strftime("%Y-%m-%d")


@st.cache_data(ttl=3600)
def fetch_prices(tickers: tuple[str, ...], start: date, end: date) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()

    data = yf.download(
        tickers=list(tickers),
        start=_to_date_str(start),
        end=_to_date_str(end),
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(0):
            closes = data["Close"].copy()
        elif "Adj Close" in data.columns.get_level_values(0):
            closes = data["Adj Close"].copy()
        else:
            closes = data.xs(data.columns.get_level_values(0)[0], axis=1, level=0)
    else:
        close_col = "Close" if "Close" in data.columns else data.columns[0]
        closes = data[[close_col]].copy()
        closes.columns = [tickers[0]]

    closes.index = pd.to_datetime(closes.index).tz_localize(None)
    return closes.sort_index().dropna(how="all")


@st.cache_data(ttl=3600)
def fetch_us_treasury_yield(label: str, start: date, end: date) -> pd.DataFrame:
    tickers = US_TREASURY_TICKERS.get(label, ())
    for ticker in tickers:
        df = yf.download(
            tickers=ticker,
            start=_to_date_str(start),
            end=_to_date_str(end),
            auto_adjust=True,
            progress=False,
        )
        if df.empty:
            continue

        close_col = "Close" if "Close" in df.columns else df.columns[0]
        out = df[[close_col]].copy()
        out.columns = [label]
        out.index = pd.to_datetime(out.index).tz_localize(None)
        out = out.sort_index().dropna(how="all")
        if not out.empty:
            return out

    return pd.DataFrame(columns=[label])


def calc_annualized_return(series: pd.Series, start_date: date) -> float | None:
    clean = series.dropna()
    if clean.empty:
        return None

    start_ts = pd.Timestamp(start_date)
    subset = clean[clean.index >= start_ts]
    if subset.empty:
        return None

    start_value = float(subset.iloc[0])
    end_value = float(clean.iloc[-1])
    start_idx = subset.index[0]
    end_idx = clean.index[-1]
    total_days = (end_idx - start_idx).days

    if start_value <= 0 or end_value <= 0 or total_days <= 0:
        return None

    years = total_days / 365.25
    return (end_value / start_value) ** (1 / years) - 1


@st.cache_data(ttl=1800)
def fetch_ticker_news(ticker: str, limit: int = 8) -> list[dict[str, str]]:
    try:
        news_items = yf.Ticker(ticker).news or []
    except Exception:
        return []

    parsed: list[dict[str, str]] = []
    for item in news_items[:limit]:
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, dict):
            title = str(content.get("title") or "Untitled")
            link = str(
                content.get("canonicalUrl", {}).get("url")
                or content.get("clickThroughUrl", {}).get("url")
                or ""
            )
            source = str(content.get("provider", {}).get("displayName") or "Unknown source")
            published_at = str(content.get("pubDate") or "")
        else:
            title = str(item.get("title") or "Untitled") if isinstance(item, dict) else "Untitled"
            link = str(item.get("link") or "") if isinstance(item, dict) else ""
            source = str(item.get("publisher") or "Unknown source") if isinstance(item, dict) else "Unknown source"
            published_at = ""

        parsed.append(
            {
                "title": title,
                "link": link,
                "source": source,
                "published_at": published_at,
            }
        )

    return parsed


@st.cache_data(ttl=1800)
def fetch_ticker_kpis(ticker: str) -> dict[str, float | str | None]:
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        return {
            "trailing_pe": None,
            "market_cap": None,
            "ebitda": None,
            "market_cap_to_ebitda": None,
            "enterprise_to_ebitda": None,
            "total_debt": None,
            "debt_to_ebitda": None,
            "dividend_payment": None,
            "dividend_yield": None,
            "currency": None,
            "quote_type": None,
        }

    market_cap = info.get("marketCap")
    ebitda = info.get("ebitda")
    total_debt = info.get("totalDebt")
    dividend_payment = info.get("dividendRate")
    if not isinstance(dividend_payment, (int, float)):
        dividend_payment = info.get("lastDividendValue")
    dividend_yield = info.get("dividendYield")

    market_cap_to_ebitda: float | None = None
    if isinstance(market_cap, (int, float)) and isinstance(ebitda, (int, float)) and ebitda not in (0, None):
        market_cap_to_ebitda = float(market_cap) / float(ebitda)

    debt_to_ebitda: float | None = None
    if isinstance(total_debt, (int, float)) and isinstance(ebitda, (int, float)) and ebitda not in (0, None):
        debt_to_ebitda = float(total_debt) / float(ebitda)

    trailing_pe = info.get("trailingPE")
    enterprise_to_ebitda = info.get("enterpriseToEbitda")

    return {
        "trailing_pe": float(trailing_pe) if isinstance(trailing_pe, (int, float)) else None,
        "market_cap": float(market_cap) if isinstance(market_cap, (int, float)) else None,
        "ebitda": float(ebitda) if isinstance(ebitda, (int, float)) else None,
        "market_cap_to_ebitda": market_cap_to_ebitda,
        "enterprise_to_ebitda": float(enterprise_to_ebitda)
        if isinstance(enterprise_to_ebitda, (int, float))
        else None,
        "total_debt": float(total_debt) if isinstance(total_debt, (int, float)) else None,
        "debt_to_ebitda": debt_to_ebitda,
        "dividend_payment": float(dividend_payment) if isinstance(dividend_payment, (int, float)) else None,
        "dividend_yield": float(dividend_yield) if isinstance(dividend_yield, (int, float)) else None,
        "currency": str(info.get("currency") or ""),
        "quote_type": str(info.get("quoteType") or ""),
    }
