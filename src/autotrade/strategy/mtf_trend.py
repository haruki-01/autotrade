from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from autotrade.strategy.common import (
    Bias,
    default_exit_flags,
    ema_bias_frames,
    merge_htf_bias,
)


@dataclass
class StrategyParams:
    daily_ema: int = 50
    h4_ema: int = 20
    m15_ema: int = 20
    stop_loss_pct: float = 1.0
    take_profit_pct: float = 1.5


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: StrategyParams,
) -> pd.DataFrame:
    """H01 — MTF EMA pullback with fixed % stop/TP."""
    d, h, m = ema_bias_frames(
        daily,
        h4,
        m15,
        daily_ema=params.daily_ema,
        h4_ema=params.h4_ema,
        m15_ema=params.m15_ema,
    )
    merged = merge_htf_bias(m, d, h)
    merged = default_exit_flags(merged)

    long_ok = (merged["daily_bias"] == Bias.LONG.value) & (merged["h4_bias"] == Bias.LONG.value)
    short_ok = (merged["daily_bias"] == Bias.SHORT.value) & (merged["h4_bias"] == Bias.SHORT.value)
    merged["allow_long"] = long_ok.fillna(False)
    merged["allow_short"] = short_ok.fillna(False)

    near = (merged["low"] <= merged["m15_ema"] * 1.001) & (merged["high"] >= merged["m15_ema"] * 0.999)
    merged["long_signal"] = merged["allow_long"] & near & merged["bullish"]
    merged["short_signal"] = merged["allow_short"] & near & merged["bearish"]
    merged["stop_pct"] = params.stop_loss_pct
    merged["tp_pct"] = params.take_profit_pct
    return merged
