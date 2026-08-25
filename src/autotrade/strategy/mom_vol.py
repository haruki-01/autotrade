"""L-MOM-VOL — daily SMA200 regime, H4 EMA confirm, ATR trail, no fixed TP."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from autotrade.indicators import ema, sma
from autotrade.strategy.common import (
    Bias,
    attach_m15_atr,
    merge_htf_bias,
    norm_ohlcv,
)

@dataclass
class MomVolParams:
    daily_sma: int = 200
    h4_ema: int = 20
    atr_period: int = 14
    trail_atr_mult: float = 2.5
    stop_atr_mult: float = 1.5
    min_stop_pct: float = 0.4


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: MomVolParams | None = None,
) -> pd.DataFrame:
    params = params or MomVolParams()
    d = norm_ohlcv(daily)
    d["sma"] = sma(d["close"], params.daily_sma)
    d["daily_bias"] = Bias.NEUTRAL.value
    d.loc[d["close"] > d["sma"], "daily_bias"] = Bias.LONG.value
    d.loc[d["close"] < d["sma"], "daily_bias"] = Bias.SHORT.value

    h = norm_ohlcv(h4)
    h["h4_ema"] = ema(h["close"], params.h4_ema)
    h["h4_bias"] = Bias.NEUTRAL.value
    h.loc[(h["close"] > h["h4_ema"]) & (h["h4_ema"] > h["h4_ema"].shift(1)), "h4_bias"] = (
        Bias.LONG.value
    )
    h.loc[(h["close"] < h["h4_ema"]) & (h["h4_ema"] < h["h4_ema"].shift(1)), "h4_bias"] = (
        Bias.SHORT.value
    )

    m = attach_m15_atr(norm_ohlcv(m15), params.atr_period)
    m["m15_ema"] = ema(m["close"], 20)
    m["bullish"] = m["close"] > m["open"]
    m["bearish"] = m["close"] < m["open"]

    merged = merge_htf_bias(m, d, h)
    long_ok = (merged["daily_bias"] == Bias.LONG.value) & (merged["h4_bias"] == Bias.LONG.value)
    short_ok = (merged["daily_bias"] == Bias.SHORT.value) & (merged["h4_bias"] == Bias.SHORT.value)

    # Shallow pullback / bounce at EMA as execution trigger
    near = (merged["low"] <= merged["m15_ema"] * 1.002) & (merged["high"] >= merged["m15_ema"] * 0.998)
    merged["long_signal"] = long_ok.fillna(False) & near & merged["bullish"]
    merged["short_signal"] = short_ok.fillna(False) & near & merged["bearish"]

    atr_pct = (merged["atr"] / merged["close"] * 100.0 * params.stop_atr_mult).clip(
        lower=params.min_stop_pct
    )
    merged["stop_pct"] = atr_pct
    merged["tp_pct"] = float("nan")  # no fixed TP
    merged["trail_atr_mult"] = params.trail_atr_mult

    merged["h4_long_break"] = merged["h4_bias"] != Bias.LONG.value
    merged["h4_short_break"] = merged["h4_bias"] != Bias.SHORT.value
    merged["daily_against_long"] = merged["daily_bias"] != Bias.LONG.value
    merged["daily_against_short"] = merged["daily_bias"] != Bias.SHORT.value
    merged["structure_exit_long"] = False
    merged["structure_exit_short"] = False
    return merged
