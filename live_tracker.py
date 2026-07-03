"""
定時自動刷新的股票追蹤圖表。

用法:
    python live_tracker.py 2330 --interval 60
    python live_tracker.py AAPL --interval 30 --bar-interval 5m

注意：yfinance 的資料本身有 15-20 分鐘左右的延遲（Yahoo Finance 免費資料源的
限制），這裡的「定時刷新」是指程式多久重新抓一次資料、重畫一次圖，
不代表能看到真正的即時報價。
"""

import argparse
from datetime import datetime

import chart_style  # noqa: F401  設定中文字型
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from data_fetcher import normalize_ticker

import yfinance as yf


def fetch_intraday(ticker: str, bar_interval: str):
    df = yf.Ticker(ticker).history(period="1d", interval=bar_interval)
    if df.empty:
        # 盤前/盤後或非交易時間可能抓不到當日資料，退而求其次抓近幾天
        df = yf.Ticker(ticker).history(period="5d", interval=bar_interval)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", help="股票代號，例如 2330 或 AAPL")
    parser.add_argument("--interval", type=int, default=60, help="幾秒鐘刷新一次，預設 60 秒")
    parser.add_argument("--bar-interval", default="1m", help="K棒頻率，例如 1m, 5m，預設 1m")
    args = parser.parse_args()

    ticker = normalize_ticker(args.ticker)

    fig, (ax_price, ax_vol) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    def update(frame):
        try:
            df = fetch_intraday(ticker, args.bar_interval)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取資料失敗：{e}")
            return

        if df.empty:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 目前抓不到 {ticker} 的資料")
            return

        ax_price.clear()
        ax_vol.clear()

        latest_price = df["Close"].iloc[-1]
        open_price = df["Open"].iloc[0]
        change = latest_price - open_price
        change_pct = change / open_price * 100
        color = "red" if change >= 0 else "green"  # 台股習慣紅漲綠跌

        ax_price.plot(df.index, df["Close"], color="tab:blue", linewidth=1.5)
        ax_price.axhline(open_price, color="grey", linestyle="--", linewidth=0.8, label="今日開盤價")
        ax_price.set_ylabel("價格")
        ax_price.legend(loc="upper left")
        ax_price.set_title(
            f"{ticker}   {latest_price:.2f}   {change:+.2f} ({change_pct:+.2f}%)\n"
            f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=color,
            fontsize=13,
        )

        ax_vol.bar(df.index, df["Volume"], color="tab:orange", width=0.0006)
        ax_vol.set_ylabel("成交量")

        fig.autofmt_xdate()

    ani = FuncAnimation(fig, update, interval=args.interval * 1000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
