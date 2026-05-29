from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common.financial_data import (
    INSTRUMENT_TICKERS,
    RATE_SERIES_OPTIONS,
    calc_annualized_return,
    fetch_prices,
    fetch_ticker_kpis,
    fetch_ticker_news,
    fetch_us_treasury_yield,
)

TRAILING_RETURN_WINDOWS = [
    ("1W", 7),
    ("1M", 30),
    ("3M", 91),
    ("6M", 182),
    ("12M", 365),
    ("24M", 730),
    ("36M", 1095),
]

MAIN_CHART_HEIGHT = 1000
DETAIL_CHART_HEIGHT = 520


def _format_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.1f}%"


def _rebase_to_100(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    filled = df.ffill()
    base = filled.apply(lambda col: col.dropna().iloc[0] if not col.dropna().empty else pd.NA)
    return filled.divide(base, axis=1) * 100


def _build_return_table(prices: pd.DataFrame, start_date: date) -> pd.DataFrame:
    rows: list[dict[str, str | float]] = []
    for name in prices.columns:
        series = prices[name].dropna()
        if series.empty:
            continue

        start_ts = pd.Timestamp(start_date)
        window = series[series.index >= start_ts]
        if window.empty:
            continue

        start_price = float(window.iloc[0])
        start_date_used = window.index[0].date().isoformat()
        end_price = float(series.iloc[-1])
        end_date_used = series.index[-1].date().isoformat()
        total_return = (end_price / start_price) - 1 if start_price > 0 else None
        annualized = calc_annualized_return(series, start_date)

        rows.append(
            {
                "Instrument": name,
                "Start date": start_date_used,
                "End date": end_date_used,
                "Start price": round(start_price, 1),
                "End price": round(end_price, 1),
                "Total return": _format_pct(total_return),
                "Annualized return": _format_pct(annualized),
            }
        )

    return pd.DataFrame(rows)


def _build_rate_summary(rates: pd.DataFrame, start_date: date) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    start_ts = pd.Timestamp(start_date)
    for col in rates.columns:
        series = rates[col].dropna()
        if series.empty:
            continue

        start_window = series[series.index >= start_ts]
        if start_window.empty:
            continue

        start_value = float(start_window.iloc[0])
        current_value = float(series.iloc[-1])
        change_bps = (current_value - start_value) * 100

        rows.append(
            {
                "Rate": col,
                "Rate at start (%)": round(start_value, 1),
                "Latest rate (%)": round(current_value, 1),
                "Change (bps)": round(change_bps, 1),
            }
        )

    return pd.DataFrame(rows)


def _instrument_snapshot(series: pd.Series, start_date: date) -> dict[str, float | str] | None:
    clean = series.dropna()
    if clean.empty:
        return None

    start_window = clean[clean.index >= pd.Timestamp(start_date)]
    if start_window.empty:
        return None

    start_price = float(start_window.iloc[0])
    latest_price = float(clean.iloc[-1])
    if start_price <= 0:
        return None

    total_return = (latest_price / start_price) - 1
    relative_multiple = latest_price / start_price
    annualized_return = calc_annualized_return(clean, start_date)
    return {
        "start_price": start_price,
        "latest_price": latest_price,
        "total_return": total_return,
        "relative_multiple": relative_multiple,
        "annualized_return": annualized_return,
    }


def _build_trailing_returns(series: pd.Series) -> pd.DataFrame:
    clean = series.dropna().sort_index()
    if clean.empty:
        return pd.DataFrame(
            columns=["Period", "Start price", "Stop price", "Return", "Annualized return"]
        )

    latest_date = clean.index[-1]
    latest_price = float(clean.iloc[-1])
    rows: list[dict[str, str]] = []

    for label, days in TRAILING_RETURN_WINDOWS:
        target_date = latest_date - pd.Timedelta(days=days)
        historical = clean.loc[:target_date]
        if historical.empty:
            rows.append(
                {
                    "Period": label,
                    "Start price": "N/A",
                    "Stop price": f"{latest_price:.1f}",
                    "Return": "N/A",
                    "Annualized return": "N/A",
                }
            )
            continue

        reference_price = float(historical.iloc[-1])
        if reference_price <= 0:
            rows.append(
                {
                    "Period": label,
                    "Start price": "N/A",
                    "Stop price": f"{latest_price:.1f}",
                    "Return": "N/A",
                    "Annualized return": "N/A",
                }
            )
            continue

        trailing_return = (latest_price / reference_price) - 1
        annualized = (1 + trailing_return) ** (365.25 / days) - 1
        rows.append(
            {
                "Period": label,
                "Start price": f"{reference_price:.1f}",
                "Stop price": f"{latest_price:.1f}",
                "Return": _format_pct(trailing_return),
                "Annualized return": _format_pct(annualized),
            }
        )

    return pd.DataFrame(rows)


def _format_number(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.1f}"


def _format_large_number(value: float | None, currency: str = "") -> str:
    if value is None or pd.isna(value):
        return "N/A"

    abs_value = abs(value)
    suffix = ""
    scaled = value
    if abs_value >= 1_000_000_000_000:
        scaled = value / 1_000_000_000_000
        suffix = "T"
    elif abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = "B"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = "M"

    prefix = f"{currency} " if currency else ""
    return f"{prefix}{scaled:.1f}{suffix}"


def _build_kpi_table(kpis: dict[str, float | str | None]) -> pd.DataFrame:
    currency = str(kpis.get("currency") or "")
    rows = [
        {"KPI": "Price / Earnings (TTM)", "Value": _format_number(kpis.get("trailing_pe"))},
        {"KPI": "Market Cap", "Value": _format_large_number(kpis.get("market_cap"), currency=currency)},
        {"KPI": "Total Debt", "Value": _format_large_number(kpis.get("total_debt"), currency=currency)},
        {"KPI": "EBITDA", "Value": _format_large_number(kpis.get("ebitda"), currency=currency)},
        {"KPI": "Debt / EBITDA", "Value": _format_number(kpis.get("debt_to_ebitda"))},
        {"KPI": "Market Cap / EBITDA", "Value": _format_number(kpis.get("market_cap_to_ebitda"))},
        {
            "KPI": "Enterprise Value / EBITDA",
            "Value": _format_number(kpis.get("enterprise_to_ebitda")),
        },
        {
            "KPI": "Dividend Payment (annual/share)",
            "Value": _format_number(kpis.get("dividend_payment")),
        },
        {"KPI": "Dividend Yield", "Value": _format_pct(kpis.get("dividend_yield"))},
    ]
    return pd.DataFrame(rows)


st.title("Financial Dashboard")
st.caption("Interactive market overview with equities, indices, and key interest rates.")

today = date.today()
default_start = date(2020, 1, 1)

st.sidebar.header("Dashboard Controls")
if st.sidebar.button("Clear Cached Data", help="Refresh cached prices, KPIs, rates, and news"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

start_date = st.sidebar.date_input("Start date", value=default_start, max_value=today)

instrument_options = list(INSTRUMENT_TICKERS.keys())
selected_instruments = st.sidebar.multiselect(
    "Equities and indices",
    options=instrument_options,
    default=instrument_options,
)

selected_rates = st.sidebar.multiselect(
    "Interest rate series",
    options=RATE_SERIES_OPTIONS,
    default=RATE_SERIES_OPTIONS,
)

tab_equities, tab_rates = st.tabs(["Equities & Indices", "Interest Rates"])

with tab_equities:
    st.subheader("Performance Since Selected Date")
    if not selected_instruments:
        st.info("Select at least one equity/index in the sidebar.")
    else:
        tickers = tuple(INSTRUMENT_TICKERS[name] for name in selected_instruments)
        end_date = today + timedelta(days=1)
        try:
            prices = fetch_prices(tickers=tickers, start=start_date, end=end_date)
        except Exception as exc:
            st.error(f"Failed to fetch market prices: {exc}")
            prices = pd.DataFrame()

        if prices.empty:
            st.warning(
                "No price data was returned for the selected period. "
                "For STOXX Europe 600, try a broader date range if the symbol is temporarily unavailable."
            )
        else:
            ticker_to_label = {v: k for k, v in INSTRUMENT_TICKERS.items()}
            prices = prices.rename(columns=ticker_to_label)
            prices = prices[[c for c in selected_instruments if c in prices.columns]]
            prices = prices.loc[prices.index >= pd.Timestamp(start_date)]
            prices = prices.sort_index().dropna(how="all")
            rebased = _rebase_to_100(prices).dropna(how="all")

            if rebased.empty:
                st.warning("No usable price observations were found after filtering.")
            else:
                st.caption("Rebased Performance (Start = 100)")

                rebased_plot = rebased.reset_index().melt(
                    id_vars=rebased.index.name or "Date",
                    var_name="Instrument",
                    value_name="Indexed price",
                )
                date_col = rebased.index.name or "Date"
                fig = px.line(
                    rebased_plot,
                    x=date_col,
                    y="Indexed price",
                    color="Instrument",
                    title="Rebased Performance (Start = 100)",
                )
                fig.update_layout(
                    legend_title_text="Series",
                    yaxis_title="Index level",
                    height=MAIN_CHART_HEIGHT,
                )
                st.plotly_chart(fig, use_container_width=True)

                returns_df = _build_return_table(prices, start_date)
                st.markdown("### Return Metrics")
                st.dataframe(returns_df, use_container_width=True)

                st.markdown("### Per Instrument View")
                instrument_tabs = st.tabs(list(rebased.columns))

                for tab, instrument in zip(instrument_tabs, rebased.columns, strict=False):
                    with tab:
                        series = prices[instrument]
                        snapshot = _instrument_snapshot(series, start_date)
                        if snapshot is None:
                            st.info("Not enough data for this instrument in the selected date range.")
                            continue
                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("Start price", f"{float(snapshot['start_price']):.1f}")
                        col2.metric("Latest price", f"{float(snapshot['latest_price']):.1f}")
                        col3.metric("Return since start", _format_pct(snapshot["total_return"]))
                        col4.metric("Value vs start", f"{float(snapshot['relative_multiple']):.1f}x")
                        col5.metric("Annualized return", _format_pct(snapshot["annualized_return"]))

                        detail_df = pd.DataFrame(
                            {
                                "Date": rebased.index,
                                "Indexed value": rebased[instrument].to_numpy(),
                            }
                        )
                        fig_detail = px.line(
                            detail_df,
                            x="Date",
                            y="Indexed value",
                            title=f"{instrument}: Value Relative to Start Price (Start = 100)",
                        )
                        fig_detail.update_layout(yaxis_title="Indexed value", height=DETAIL_CHART_HEIGHT)
                        st.plotly_chart(fig_detail, use_container_width=True)

                        st.markdown("#### Latest Trailing Returns")
                        trailing_df = _build_trailing_returns(series)
                        st.dataframe(trailing_df, use_container_width=True, hide_index=True)

                        st.markdown("#### Company KPIs")
                        ticker = INSTRUMENT_TICKERS.get(instrument, "")
                        if not ticker:
                            st.info("No ticker is configured for this instrument.")
                        else:
                            kpis = fetch_ticker_kpis(ticker=ticker)
                            kpi_df = _build_kpi_table(kpis)
                            st.dataframe(kpi_df, use_container_width=True, hide_index=True)

                        st.markdown("#### Latest News")
                        if not ticker:
                            st.info("No ticker is configured for this instrument.")
                        else:
                            news = fetch_ticker_news(ticker=ticker, limit=6)
                            if not news:
                                st.info("No recent news available for this ticker.")
                            else:
                                for item in news:
                                    title = item.get("title", "Untitled")
                                    link = item.get("link", "")
                                    source = item.get("source", "Unknown source")
                                    published_at = item.get("published_at", "")
                                    timestamp = f" ({published_at})" if published_at else ""
                                    if link:
                                        st.markdown(f"- [{title}]({link}) - {source}{timestamp}")
                                    else:
                                        st.markdown(f"- {title} - {source}{timestamp}")

with tab_rates:
    st.subheader("Interest Rate Trends")
    if not selected_rates:
        st.info("Select at least one interest-rate series in the sidebar.")
    else:
        rate_frames: list[pd.DataFrame] = []
        us_treasury_labels = [
            "US 5Y Treasury yield",
            "US 10Y Treasury yield",
            "US 30Y Treasury yield",
        ]

        for label in us_treasury_labels:
            if label not in selected_rates:
                continue
            try:
                series_df = fetch_us_treasury_yield(label=label, start=start_date, end=today + timedelta(days=1))
                if not series_df.empty:
                    rate_frames.append(series_df)
                else:
                    st.warning(f"No data returned for {label}.")
            except Exception as exc:
                st.error(f"Could not load {label}: {exc}")

        if not rate_frames:
            st.warning("No interest-rate data available for the selected sources right now.")
        else:
            rates = pd.concat(rate_frames, axis=1).sort_index()
            rates = rates.loc[rates.index >= pd.Timestamp(start_date)]
            rates = rates.dropna(how="all")

            if rates.empty:
                st.warning("No rate observations found for this date range.")
            else:
                fig = go.Figure()
                for col in rates.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=rates.index,
                            y=rates[col],
                            mode="lines",
                            name=col,
                        )
                    )
                fig.update_layout(
                    title="Interest Rates (%)",
                    xaxis_title="Date",
                    yaxis_title="Percent",
                    legend_title_text="Series",
                    height=MAIN_CHART_HEIGHT,
                )
                st.plotly_chart(fig, use_container_width=True)

                summary = _build_rate_summary(rates, start_date)
                st.markdown("### Rate Summary")
                st.dataframe(summary, use_container_width=True)
