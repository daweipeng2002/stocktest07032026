"""
股票走勢分析網站（Streamlit）

啟動方式：
    streamlit run webapp.py

啟動後終端機會顯示一個網址（預設 http://localhost:8501），用瀏覽器打開即可。
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

from data_fetcher import (
    get_extended_hours_quote,
    get_fundamentals,
    get_history,
    get_quarterly_revenue,
    normalize_ticker,
)
from indicators import add_all_indicators
from plotly_charts import build_candlestick_html, build_comparison_figure, build_revenue_figure

st.set_page_config(page_title="股票走勢分析", layout="wide")

WATCHLIST = ["MRVL", "ARM", "TSLA", "SPCX", "CRWV", "MU"]
INDEXES = {"^SOX": "費城半導體指數", "^IXIC": "那斯達克指數", "^DJI": "道瓊工業指數"}


@st.cache_data(ttl=60, show_spinner=False)
def cached_history(ticker: str, period: str, interval: str):
    return get_history(ticker, period=period, interval=interval)


@st.cache_data(ttl=300, show_spinner=False)
def cached_fundamentals(ticker: str):
    return get_fundamentals(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def cached_revenue(ticker: str):
    return get_quarterly_revenue(ticker)


@st.cache_data(ttl=30, show_spinner=False)
def cached_extended_quote(ticker: str):
    return get_extended_hours_quote(ticker)


def format_extended_caption(ticker: str) -> str:
    """回傳盤前／盤後報價的顯示文字；沒有資料（例如台股、或不在盤前盤後時段）就回傳空字串。"""
    try:
        quote = cached_extended_quote(ticker)
    except Exception:
        return ""

    if quote.get("pre_price") is not None:
        chg = quote.get("pre_change") or 0
        chg_pct = quote.get("pre_change_percent") or 0
        return f"🌤️ 盤前 {quote['pre_price']:.2f}（{chg:+.2f}, {chg_pct:+.2f}%）"

    if quote.get("post_price") is not None:
        chg = quote.get("post_change") or 0
        chg_pct = quote.get("post_change_percent") or 0
        return f"🌙 盤後 {quote['post_price']:.2f}（{chg:+.2f}, {chg_pct:+.2f}%）"

    return ""


st.title("📈 股票走勢分析")

index_header_col, index_toggle_col, index_interval_col = st.columns([2, 1, 1])
with index_header_col:
    st.subheader("🌎 大盤指數即時追蹤")
with index_toggle_col:
    index_auto_refresh = st.checkbox("自動刷新", value=True, key="index_auto_refresh")
with index_interval_col:
    index_refresh_seconds = st.number_input(
        "刷新間隔（秒）", min_value=15, max_value=600, value=30, step=15,
        disabled=not index_auto_refresh, key="index_refresh_seconds",
    )

if index_auto_refresh:
    st_autorefresh(interval=index_refresh_seconds * 1000, key="index_autorefresh")

index_cols = st.columns(len(INDEXES))
for col, (symbol, name) in zip(index_cols, INDEXES.items()):
    with col:
        try:
            idx_df = cached_history(symbol, "5d", "1d")
            idx_last = idx_df["Close"].iloc[-1]
            idx_prev = idx_df["Close"].iloc[-2] if len(idx_df) > 1 else idx_last
            idx_change = idx_last - idx_prev
            idx_change_pct = idx_change / idx_prev * 100 if idx_prev else 0
            col.metric(name, f"{idx_last:,.2f}", f"{idx_change:+.2f} ({idx_change_pct:+.2f}%)")
        except Exception as e:
            col.metric(name, "N/A")
            col.caption(f"抓取失敗：{e}")

st.divider()

tab_analyze, tab_compare = st.tabs(["個股分析", "多檔比較"])

if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = WATCHLIST[0]

with tab_analyze:
    st.caption("⭐ 自選股快速切換")
    watch_cols = st.columns(len(WATCHLIST))
    for i, wt in enumerate(WATCHLIST):
        with watch_cols[i]:
            try:
                wt_df = cached_history(normalize_ticker(wt), "5d", "1d")
                wt_last = wt_df["Close"].iloc[-1]
                wt_prev = wt_df["Close"].iloc[-2] if len(wt_df) > 1 else wt_last
                wt_change_pct = (wt_last - wt_prev) / wt_prev * 100 if wt_prev else 0
                st.metric(wt, f"{wt_last:.2f}", f"{wt_change_pct:+.2f}%")
                extended = format_extended_caption(normalize_ticker(wt))
                if extended:
                    st.caption(extended)
            except Exception:
                st.metric(wt, "N/A")
            if st.button("查看", key=f"select_{wt}", use_container_width=True):
                st.session_state.ticker_input = wt
                st.rerun()

    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    with col1:
        ticker_input = st.text_input(
            "股票代號", key="ticker_input",
            help="台股輸入純數字會自動補 .TW，例如 2330；美股直接輸入 AAPL",
        )
    with col2:
        period = st.selectbox("資料期間", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    with col3:
        interval = st.selectbox("資料頻率", ["1d", "1wk"], index=0)
    with col4:
        auto_refresh = st.checkbox("自動定時刷新", value=False)
        refresh_seconds = st.number_input(
            "刷新間隔（秒）", min_value=15, max_value=600, value=60, step=15, disabled=not auto_refresh
        )

    if auto_refresh:
        st_autorefresh(interval=refresh_seconds * 1000, key="analyze_autorefresh")

    if ticker_input:
        ticker = normalize_ticker(ticker_input)
        try:
            with st.spinner(f"抓取 {ticker} 資料中..."):
                df = cached_history(ticker, period, interval)
                df = add_all_indicators(df)
                info = cached_fundamentals(ticker_input)
                revenue = cached_revenue(ticker_input)

            latest = df.iloc[-1]
            prev_close = df["Close"].iloc[-2] if len(df) > 1 else latest["Close"]
            change = latest["Close"] - prev_close
            change_pct = change / prev_close * 100 if prev_close else 0

            m1, m2 = st.columns(2)
            is_tw_stock = ticker.endswith((".TW", ".TWO"))
            m1.metric(
                "最新收盤價", f"{latest['Close']:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)",
                delta_color="inverse" if is_tw_stock else "normal",  # 台股慣例：紅漲綠跌
            )
            m2.metric("成交量", f"{latest['Volume']:,.0f}")

            extended = format_extended_caption(ticker)
            if extended:
                st.caption(extended)

            chart_html, chart_height = build_candlestick_html(df, ticker)
            components.html(chart_html, height=chart_height + 40, scrolling=False)

            st.subheader("基本面摘要")
            info_cols = st.columns(4)
            for i, (k, v) in enumerate(info.items()):
                info_cols[i % 4].metric(k, v)

            if not revenue.empty:
                st.subheader("近幾季營收")
                st.plotly_chart(build_revenue_figure(revenue.tail(8)), use_container_width=True)

        except Exception as e:
            st.error(f"發生錯誤：{e}")

with tab_compare:
    tickers_input = st.text_input("多個股票代號（用空格或逗號分隔）", value=" ".join(WATCHLIST))
    compare_period = st.selectbox("資料期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2, key="compare_period")

    if tickers_input:
        raw_tickers = [t.strip() for t in tickers_input.replace(",", " ").split() if t.strip()]
        price_dict = {}
        errors = []

        for raw in raw_tickers:
            ticker = normalize_ticker(raw)
            try:
                with st.spinner(f"抓取 {ticker} 資料中..."):
                    df = cached_history(ticker, compare_period, "1d")
                price_dict[ticker] = df["Close"]
            except Exception as e:
                errors.append(f"{ticker}: {e}")

        if errors:
            st.warning("\n".join(errors))

        if price_dict:
            fig = build_comparison_figure(price_dict)
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
