"""常用技術指標計算：移動平均、RSI、MACD。純 pandas 實作，不依賴 ta-lib。"""

import pandas as pd


def add_sma(df: pd.DataFrame, windows=(5, 20, 60)) -> pd.DataFrame:
    df = df.copy()
    for w in windows:
        df[f"SMA{w}"] = df["Close"].rolling(window=w).mean()
    return df


def add_ema(df: pd.DataFrame, windows=(12, 26)) -> pd.DataFrame:
    df = df.copy()
    for w in windows:
        df[f"EMA{w}"] = df["Close"].ewm(span=w, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, "RSI"] = 100
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    df = df.copy()
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sma(df)
    df = add_rsi(df)
    df = add_macd(df)
    return df
