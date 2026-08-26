from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev = close.shift(1)
    ranges = pd.concat(
        [
            (high - low).abs(),
            (high - prev).abs(),
            (low - prev).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    return true_range(high, low, close).rolling(window=period, min_periods=period).mean()


def donchian_high(high: pd.Series, window: int) -> pd.Series:
    # Prior window only (no lookahead on current bar)
    return high.shift(1).rolling(window=window, min_periods=window).max()


def donchian_low(low: pd.Series, window: int) -> pd.Series:
    return low.shift(1).rolling(window=window, min_periods=window).min()
