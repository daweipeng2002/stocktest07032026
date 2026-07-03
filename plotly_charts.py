"""用 Plotly 畫互動式圖表（網頁版專用，瀏覽器原生支援中文字型，不會有 matplotlib 那種缺字問題）。"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_candlestick_figure(df: pd.DataFrame, ticker: str) -> go.Figure:
    # 台股慣例：紅漲綠跌；其他市場（美股等）維持國際慣例：綠漲紅跌
    is_tw_stock = ticker.endswith((".TW", ".TWO"))
    up_color, down_color = ("red", "green") if is_tw_stock else ("green", "red")

    rows = 2
    row_heights = [0.7, 0.3]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.1,
        row_heights=row_heights, subplot_titles=["K線與均線", "成交量"],
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="K線", increasing_line_color=up_color, decreasing_line_color=down_color,
    ), row=1, col=1)

    for col in [c for c in df.columns if c.startswith("SMA")]:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, line=dict(width=1.2)), row=1, col=1)

    vol_colors = [up_color if c >= o else down_color for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量", marker_color=vol_colors), row=2, col=1)

    fig.update_layout(
        title=f"{ticker} 走勢圖",
        height=280 * rows,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        margin=dict(t=60, b=30),
    )

    # 每個面板都顯示日期刻度，不要只靠 shared_xaxes 預設把日期擠在最下面那格
    fig.update_xaxes(showticklabels=True, tickformat="%Y-%m-%d", tickangle=0, tickfont=dict(size=10))

    return fig


def build_comparison_figure(price_dict: dict, title: str = "股價報酬率比較（基期=100）") -> go.Figure:
    fig = go.Figure()
    for ticker, series in price_dict.items():
        series = series.dropna()
        normalized = series / series.iloc[0] * 100
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized.values, name=ticker, mode="lines"))

    fig.add_hline(y=100, line_dash="dash", line_color="grey")
    fig.update_layout(
        title=title,
        yaxis_title="相對報酬率（起點=100）",
        height=550,
        margin=dict(t=60, b=30),
    )
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-30, nticks=15, showgrid=True)
    return fig
