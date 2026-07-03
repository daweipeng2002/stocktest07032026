"""負責從 yfinance 抓取股價歷史資料與基本面資料。"""

import pandas as pd
import yfinance as yf


def normalize_ticker(ticker: str) -> str:
    """
    方便輸入：純數字自動視為台股，補上 .TW 後綴。
    例如 "2330" -> "2330.TW"；已經帶後綴或英文代號的維持原樣。
    """
    ticker = ticker.strip().upper()
    if ticker.isdigit():
        return f"{ticker}.TW"
    return ticker


def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    取得歷史 OHLCV 資料。
    period 例如: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    interval 例如: 1d, 1wk, 1mo
    """
    symbol = normalize_ticker(ticker)
    df = yf.Ticker(symbol).history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"抓不到 {symbol} 的歷史資料，請確認代號是否正確。")

    df = df.rename(columns={
        "Open": "Open", "High": "High", "Low": "Low",
        "Close": "Close", "Volume": "Volume",
    })
    return df[["Open", "High", "Low", "Close", "Volume"]]


def get_fundamentals(ticker: str) -> dict:
    """取得基本面摘要資料（本益比、殖利率、市值、營收成長率等）。"""
    symbol = normalize_ticker(ticker)
    info = yf.Ticker(symbol).info

    def pct(x):
        return f"{x * 100:.2f}%" if isinstance(x, (int, float)) else "N/A"

    def num(x):
        return f"{x:,.2f}" if isinstance(x, (int, float)) else "N/A"

    return {
        "代號": symbol,
        "公司名稱": info.get("longName") or info.get("shortName") or "N/A",
        "產業": info.get("industry", "N/A"),
        "目前股價": num(info.get("currentPrice") or info.get("regularMarketPrice")),
        "貨幣": info.get("currency", "N/A"),
        "市值": num(info.get("marketCap")),
        "本益比(PE)": num(info.get("trailingPE")),
        "預估本益比(Forward PE)": num(info.get("forwardPE")),
        "股價淨值比(PB)": num(info.get("priceToBook")),
        "殖利率": f"{info['dividendYield']:.2f}%" if isinstance(info.get("dividendYield"), (int, float)) else "N/A",
        "營收成長率(YoY)": pct(info.get("revenueGrowth")),
        "毛利率": pct(info.get("grossMargins")),
        "營業利益率": pct(info.get("operatingMargins")),
        "52週最高": num(info.get("fiftyTwoWeekHigh")),
        "52週最低": num(info.get("fiftyTwoWeekLow")),
    }


def get_extended_hours_quote(ticker: str) -> dict:
    """
    取得盤前/盤後即時報價（美股才有意義；台股沒有盤前盤後交易，欄位會是 None）。
    marketState 常見值：PRE（盤前）, REGULAR（盤中）, POST/POSTPOST（盤後）, CLOSED（已收盤）。
    """
    symbol = normalize_ticker(ticker)
    info = yf.Ticker(symbol).info

    return {
        "market_state": info.get("marketState"),
        "regular_price": info.get("regularMarketPrice"),
        "pre_price": info.get("preMarketPrice"),
        "pre_change": info.get("preMarketChange"),
        "pre_change_percent": info.get("preMarketChangePercent"),
        "post_price": info.get("postMarketPrice"),
        "post_change": info.get("postMarketChange"),
        "post_change_percent": info.get("postMarketChangePercent"),
    }


def get_quarterly_revenue(ticker: str) -> pd.DataFrame:
    """取得近幾季的營收資料。"""
    symbol = normalize_ticker(ticker)
    fin = yf.Ticker(symbol).quarterly_financials
    if fin.empty or "Total Revenue" not in fin.index:
        return pd.DataFrame()
    revenue = fin.loc["Total Revenue"].sort_index()
    return revenue.to_frame(name="Revenue")
