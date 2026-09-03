"""H-D: RSI exit oversold + first pull entry signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.b06_metrics import rsi_exit_os
from scripts.phase0.common import add_features
from scripts.phase1.common import RR_RATIO, Signal


def _risk_width(entry: float, atr: float) -> float:
    return max(entry * 0.008, 0.5 * atr)


def generate_hd_pull_signals(
    df: pd.DataFrame,
    weekend_filter: bool = False,
    cooldown: int = 48,
    mode: str = "pull",
) -> list[Signal]:
    """
    mode: pull = wait for first pull (H-D), raw = enter on RSI exit bar (control).
    """
    df = add_features(df)
    rsi_idx = rsi_exit_os(df)
    signals: list[Signal] = []
    last_bar = -cooldown

    for idx in rsi_idx:
        i = df.index.get_loc(idx)
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue

        if mode == "raw":
            entry_i = i
        else:
            if i + 12 >= len(df):
                continue
            window = df.iloc[i + 1 : i + 13]
            if window.empty:
                continue
            entry_i = df.index.get_loc(window["low"].idxmin())

        entry = float(df["close"].iloc[entry_i])
        atr = df["atr14"].iloc[entry_i]
        if np.isnan(atr) or atr <= 0:
            continue
        r = _risk_width(entry, atr)
        signals.append(
            Signal(
                bar_idx=entry_i,
                direction=1,
                entry_price=entry,
                sl_price=entry - r,
                tp_price=entry + RR_RATIO * r,
                max_bars=48,
                tag="hd_pull" if mode == "pull" else "hd_raw",
            )
        )
        last_bar = entry_i

    return signals
