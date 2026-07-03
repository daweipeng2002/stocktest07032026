"""用 mplfinance 畫 K 線圖，疊加均線、RSI、MACD 副圖。"""

import chart_style  # noqa: F401  設定中文字型
import mplfinance as mpf
import pandas as pd


def plot_candlestick(df: pd.DataFrame, ticker: str, title: str = None):
    sma_cols = [c for c in df.columns if c.startswith("SMA")]
    add_plots = []

    for col in sma_cols:
        add_plots.append(mpf.make_addplot(df[col], panel=0, width=1))

    panel_id = 2  # panel 0 = 主圖K線, panel 1 = 成交量
    panel_ratios = [3, 1]

    if "RSI" in df.columns:
        add_plots.append(mpf.make_addplot(
            df["RSI"], panel=panel_id, ylabel="RSI", color="purple", secondary_y=False
        ))
        add_plots.append(mpf.make_addplot(
            pd.Series(70, index=df.index), panel=panel_id, color="grey",
            linestyle="--", width=0.8, secondary_y=False,
        ))
        add_plots.append(mpf.make_addplot(
            pd.Series(30, index=df.index), panel=panel_id, color="grey",
            linestyle="--", width=0.8, secondary_y=False,
        ))
        panel_ratios.append(1)
        panel_id += 1

    if "MACD" in df.columns:
        add_plots.append(mpf.make_addplot(
            df["MACD"], panel=panel_id, ylabel="MACD", color="blue", secondary_y=False
        ))
        add_plots.append(mpf.make_addplot(
            df["MACD_signal"], panel=panel_id, color="orange", secondary_y=False
        ))
        colors = ["g" if v >= 0 else "r" for v in df["MACD_hist"]]
        add_plots.append(mpf.make_addplot(
            df["MACD_hist"], panel=panel_id, type="bar", color=colors, alpha=0.5, secondary_y=False
        ))
        panel_ratios.append(1)
        panel_id += 1

    cn_style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        rc={"font.family": "sans-serif", "font.sans-serif": ["Microsoft JhengHei", "Microsoft YaHei"]},
    )

    mpf.plot(
        df,
        type="candle",
        style=cn_style,
        title=title or ticker,
        volume=True,
        addplot=add_plots,
        panel_ratios=tuple(panel_ratios),
        figsize=(12, 9),
        tight_layout=True,
    )
    mpf.show()


def plot_comparison(price_dict: dict, title: str = "股價報酬率比較（基期=100）"):
    """
    price_dict: {ticker: Series(收盤價)}，會自動對齊時間並轉成以起點為 100 的相對報酬率。
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 6))
    for ticker, series in price_dict.items():
        series = series.dropna()
        normalized = series / series.iloc[0] * 100
        ax.plot(normalized.index, normalized.values, label=ticker, linewidth=1.8)

    ax.set_title(title)
    ax.set_ylabel("相對報酬率（起點=100）")
    ax.axhline(100, color="grey", linestyle="--", linewidth=0.8)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
