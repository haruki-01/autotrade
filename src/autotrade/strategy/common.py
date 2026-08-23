"""Shared helpers for multi-timeframe frame preparation."""

from __future__ import annotations

from enum import Enum

import pandas as pd

from autotrade.indicators import atr, ema


class Bias(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


def trend_from_ema(close: pd.Series, span: int) -> pd.Series:
    ma = ema(close, span)
    up = (close > ma) & (ma > ma.shift(1))
    down = (close < ma) & (ma < ma.shift(1))
    out = pd.Series(Bias.NEUTRAL.value, index=close.index)
    out = out.mask(up, Bias.LONG.value)
    out = out.mask(down, Bias.SHORT.value)
    return out


def norm_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.index = pd.to_datetime(out.index, utc=True).as_unit("ns")
    return out.sort_index()


def merge_htf_bias(
    m15: pd.DataFrame,
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    *,
    daily_col: str = "daily_bias",
    h4_col: str = "h4_bias",
) -> pd.DataFrame:
    """Attach confirmed HTF columns onto 15m bars (no lookahead)."""
    daily_shift = daily[[daily_col]].copy()
    daily_shift.index = daily_shift.index + pd.Timedelta(days=1)
    h4_shift = h4[[h4_col]].copy()
    h4_shift.index = h4_shift.index + pd.Timedelta(hours=4)

    base = m15.reset_index()
    daily_shift = daily_shift.reset_index()
    h4_shift = h4_shift.reset_index()

    merged = pd.merge_asof(
        base.sort_values("timestamp"),
        daily_shift.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )
    merged = pd.merge_asof(
        merged.sort_values("timestamp"),
        h4_shift.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )
    return merged.set_index("timestamp")


def merge_series_asof(
    m15: pd.DataFrame,
    higher: pd.DataFrame,
    cols: list[str],
    *,
    shift: pd.Timedelta,
) -> pd.DataFrame:
    block = higher[cols].copy()
    block.index = block.index + shift
    left = m15.reset_index()
    right = block.reset_index()
    out = pd.merge_asof(
        left.sort_values("timestamp"),
        right.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )
    return out.set_index("timestamp")


def attach_m15_atr(m15: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = m15.copy()
    out["atr"] = atr(out["high"], out["low"], out["close"], period)
    return out


def ema_bias_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    daily_ema: int,
    h4_ema: int,
    m15_ema: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    d = norm_ohlcv(daily)
    d["daily_bias"] = trend_from_ema(d["close"], daily_ema)
    h = norm_ohlcv(h4)
    h["h4_bias"] = trend_from_ema(h["close"], h4_ema)
    m = norm_ohlcv(m15)
    m["m15_ema"] = ema(m["close"], m15_ema)
    m["bullish"] = m["close"] > m["open"]
    m["bearish"] = m["close"] < m["open"]
    m = attach_m15_atr(m)
    return d, h, m


def default_exit_flags(merged: pd.DataFrame) -> pd.DataFrame:
    merged = merged.copy()
    merged["h4_long_break"] = merged["h4_bias"] != Bias.LONG.value
    merged["h4_short_break"] = merged["h4_bias"] != Bias.SHORT.value
    merged["daily_against_long"] = merged["daily_bias"] != Bias.LONG.value
    merged["daily_against_short"] = merged["daily_bias"] != Bias.SHORT.value
    merged["structure_exit_long"] = False
    merged["structure_exit_short"] = False
    return merged
