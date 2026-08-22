from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from autotrade.indicators import ema


class Bias(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


@dataclass
class StrategyParams:
    daily_ema: int = 50
    h4_ema: int = 20
    m15_ema: int = 20
    stop_loss_pct: float = 1.0
    take_profit_pct: float = 1.5


def _trend_from_ema(close: pd.Series, span: int) -> pd.Series:
    ma = ema(close, span)
    up = (close > ma) & (ma > ma.shift(1))
    down = (close < ma) & (ma < ma.shift(1))
    out = pd.Series(Bias.NEUTRAL.value, index=close.index)
    out = out.mask(up, Bias.LONG.value)
    out = out.mask(down, Bias.SHORT.value)
    return out


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: StrategyParams,
) -> pd.DataFrame:
    """Align higher-TF bias onto 15m bars using only confirmed (past) candles.

    For a 15m bar at time T, we use the latest fully closed higher-TF candle
    whose start is strictly before T (no lookahead on the current forming HTF bar).
    """
    def _norm(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out.index = pd.to_datetime(out.index, utc=True).as_unit("ns")
        return out.sort_index()

    d = _norm(daily)
    d["daily_bias"] = _trend_from_ema(d["close"], params.daily_ema)

    h = _norm(h4)
    h["h4_bias"] = _trend_from_ema(h["close"], params.h4_ema)

    m = _norm(m15)
    m["m15_ema"] = ema(m["close"], params.m15_ema)
    m["bullish"] = m["close"] > m["open"]
    m["bearish"] = m["close"] < m["open"]

    # shift(1): at time T, only use HTF candles that started earlier than T
    # merge_asof with direction='backward' on shifted index achieves confirmed HTF.
    daily_bias = d[["daily_bias"]].copy()
    daily_bias.index = daily_bias.index + pd.Timedelta(days=1)
    h4_bias = h[["h4_bias"]].copy()
    h4_bias.index = h4_bias.index + pd.Timedelta(hours=4)

    base = m.reset_index()
    daily_bias = daily_bias.reset_index().rename(columns={"timestamp": "timestamp"})
    h4_bias = h4_bias.reset_index().rename(columns={"timestamp": "timestamp"})

    merged = pd.merge_asof(
        base.sort_values("timestamp"),
        daily_bias.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )
    merged = pd.merge_asof(
        merged.sort_values("timestamp"),
        h4_bias.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )
    merged = merged.set_index("timestamp")

    long_ok = (merged["daily_bias"] == Bias.LONG.value) & (merged["h4_bias"] == Bias.LONG.value)
    short_ok = (merged["daily_bias"] == Bias.SHORT.value) & (merged["h4_bias"] == Bias.SHORT.value)
    merged["allow_long"] = long_ok.fillna(False)
    merged["allow_short"] = short_ok.fillna(False)

    # Pullback / bounce around 15m EMA
    near = (merged["low"] <= merged["m15_ema"] * 1.001) & (merged["high"] >= merged["m15_ema"] * 0.999)
    merged["long_signal"] = merged["allow_long"] & near & merged["bullish"]
    merged["short_signal"] = merged["allow_short"] & near & merged["bearish"]
    merged["h4_long_break"] = merged["h4_bias"] != Bias.LONG.value
    merged["h4_short_break"] = merged["h4_bias"] != Bias.SHORT.value
    merged["daily_against_long"] = merged["daily_bias"] != Bias.LONG.value
    merged["daily_against_short"] = merged["daily_bias"] != Bias.SHORT.value
    return merged
