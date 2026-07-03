"""
股票資料抓取分析工具

用法:
    分析單一股票（K線 + 均線 + RSI + MACD + 基本面）:
        python main.py analyze 2330 --period 1y
        python main.py analyze AAPL --period 6mo

    多檔股票報酬率比較:
        python main.py compare 2330 0050 AAPL --period 1y

台股輸入純數字會自動補上 .TW（例如 2330 -> 2330.TW）；
上櫃股票請直接輸入完整代號，例如 6488.TWO。
"""

import argparse

from data_fetcher import get_fundamentals, get_history, get_quarterly_revenue, normalize_ticker
from indicators import add_all_indicators
from plotting import plot_candlestick, plot_comparison


def print_fundamentals(ticker: str):
    print(f"\n===== {ticker} 基本面摘要 =====")
    info = get_fundamentals(ticker)
    for k, v in info.items():
        print(f"  {k}: {v}")

    revenue = get_quarterly_revenue(ticker)
    if not revenue.empty:
        print("\n  近幾季營收:")
        for date, row in revenue.tail(4).iterrows():
            print(f"    {date.date()}: {row['Revenue']:,.0f}")
    print()


def cmd_analyze(args):
    ticker = normalize_ticker(args.ticker)
    print(f"抓取 {ticker} 歷史資料中...")
    df = get_history(ticker, period=args.period, interval=args.interval)
    df = add_all_indicators(df)

    print_fundamentals(args.ticker)

    print(f"最新收盤價：{df['Close'].iloc[-1]:.2f}（{df.index[-1].date()}）")
    print(f"最新 RSI(14)：{df['RSI'].iloc[-1]:.1f}")
    print(f"最新 MACD：{df['MACD'].iloc[-1]:.3f} / 訊號線：{df['MACD_signal'].iloc[-1]:.3f}")

    plot_candlestick(df, ticker, title=f"{ticker} K線圖與技術指標")


def cmd_compare(args):
    price_dict = {}
    for raw_ticker in args.tickers:
        ticker = normalize_ticker(raw_ticker)
        print(f"抓取 {ticker} 歷史資料中...")
        df = get_history(ticker, period=args.period)
        price_dict[ticker] = df["Close"]

    plot_comparison(price_dict)


def main():
    parser = argparse.ArgumentParser(description="股票資料抓取分析工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_analyze = subparsers.add_parser("analyze", help="分析單一股票")
    p_analyze.add_argument("ticker", help="股票代號，例如 2330 或 AAPL")
    p_analyze.add_argument("--period", default="1y", help="資料期間，例如 3mo, 6mo, 1y, 2y, 5y")
    p_analyze.add_argument("--interval", default="1d", help="資料頻率，例如 1d, 1wk")
    p_analyze.set_defaults(func=cmd_analyze)

    p_compare = subparsers.add_parser("compare", help="多檔股票報酬率比較")
    p_compare.add_argument("tickers", nargs="+", help="多個股票代號，例如 2330 0050 AAPL")
    p_compare.add_argument("--period", default="1y", help="資料期間")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
