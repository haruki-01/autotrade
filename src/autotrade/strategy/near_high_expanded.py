"""SPOT-R001 — near 20d high + expanded ATR% + above SMA50."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from autotrade.indicators import atr, donchian_high, donchian_low, sma
from autotrade.strategy.common import merge_series_asof, norm_ohlcv


@dataclass
class NearHighExpandedParams:
    entry_window: int = 20
    exit_window: int = 10
    atr_period: int = 14
    sma_period: int = 50
    near_high_q: float = 0.85
    expand_mult: float = 1.25
    stop_atr_mult: float = 2.0
    min_stop_pct: float = 0.5
    new_signal_only: bool = True


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: NearHighExpandedParams | None = None,
) -> pd.DataFrame:
    params = params or NearHighExpandedParams()
    d = norm_ohlcv(daily)
    d["dc_hi"] = donchian_high(d["high"], params.entry_window)
    d["dc_lo"] = donchian_low(d["low"], params.entry_window)
    d["dc_exit_lo"] = donchian_low(d["low"], params.exit_window)
    d["daily_atr"] = atr(d["high"], d["low"], d["close"], params.atr_period)
    d["sma"] = sma(d["close"], params.sma_period)

    prev_c = d["close"].shift(1)
    tr = pd.concat(
        [
            d["high"] - d["low"],
            (d["high"] - prev_c).abs(),
            (d["low"] - prev_c).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_pct = tr.rolling(params.atr_period).mean() / d["close"]
    atr_sma = atr_pct.rolling(20).mean()
    rng = (d["dc_hi"] - d["dc_lo"]).replace(0, np.nan)
    pos = (d["close"] - d["dc_lo"]) / rng

    cond = (
        (pos > params.near_high_q)
        & (atr_pct > atr_sma * params.expand_mult)
        & (d["close"] > d["sma"])
    )
    d["setup"] = cond.fillna(False)
    d["setup_sig"] = d["setup"] & ~d["setup"].shift(1).fillna(False)
    d["exit_long"] = d["close"] < d["dc_exit_lo"]

    h = norm_ohlcv(h4)
    h["h4_confirm"] = h["close"] > h["open"]
    m = norm_ohlcv(m15)

    cols = ["setup", "setup_sig", "exit_long", "daily_atr"]
    merged = merge_series_asof(m, d, cols, shift=pd.Timedelta(days=1))
    merged = merge_series_asof(
        merged, h, ["h4_confirm"], shift=pd.Timedelta(hours=4)
    )
    day = merged.index.floor("D")
    first_bar = ~pd.Series(day, index=merged.index).duplicated(keep="first")
    base = merged["setup_sig"] if params.new_signal_only else merged["setup"]
    merged["long_signal"] = (
        base.fillna(False) & first_bar & merged["h4_confirm"].fillna(False)
    )
    merged["short_signal"] = False

    atr_pct_stop = (
        merged["daily_atr"] / merged["close"] * 100.0 * params.stop_atr_mult
    ).clip(lower=params.min_stop_pct)
    merged["atr"] = merged["daily_atr"]
    merged["stop_pct"] = atr_pct_stop.fillna(params.min_stop_pct)
    merged["tp_pct"] = float("nan")
    merged["trail_atr_mult"] = float("nan")
    merged["structure_exit_long"] = merged["exit_long"].fillna(False)
    merged["structure_exit_short"] = False
    merged["h4_long_break"] = False
    merged["h4_short_break"] = False
    merged["daily_against_long"] = False
    merged["daily_against_short"] = False
    return merged
