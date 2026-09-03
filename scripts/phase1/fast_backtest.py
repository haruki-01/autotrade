"""Fast theoretical trade outcomes for grid search."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase1.common import POSITION_Q, Signal, crosses_lev_fee_window


def fast_theoretical_outcome(df: pd.DataFrame, sig: Signal) -> tuple[float, float, int]:
    """Return (pnl_jpy, ret_pct, exit_bar_idx). Skips if insufficient bars."""
    i = sig.bar_idx
    end = min(i + sig.max_bars, len(df) - 1)
    if end <= i:
        return 0.0, 0.0, i

    direction = sig.direction
    entry = sig.entry_price
    entry_time = df["open_time"].iloc[i]

    for j in range(i + 1, end + 1):
        hi = df["high"].iloc[j]
        lo = df["low"].iloc[j]
        if direction == 1:
            if lo <= sig.sl_price:
                exit_price, reason = sig.sl_price, "sl"
                exit_bar = j
                break
            if hi >= sig.tp_price:
                exit_price, reason = sig.tp_price, "tp"
                exit_bar = j
                break
        else:
            if hi >= sig.sl_price:
                exit_price, reason = sig.sl_price, "sl"
                exit_bar = j
                break
            if lo <= sig.tp_price:
                exit_price, reason = sig.tp_price, "tp"
                exit_bar = j
                break
    else:
        exit_bar = end
        exit_price = df["close"].iloc[exit_bar]
        reason = "timeout"

    exit_time = df["open_time"].iloc[exit_bar]
    ret = direction * (exit_price / entry - 1)
    lev = POSITION_Q * 0.0004 * crosses_lev_fee_window(entry_time, exit_time)
    pnl = POSITION_Q * ret - lev
    return pnl, ret, exit_bar


def fast_run_theoretical(df: pd.DataFrame, signals: list[Signal]) -> list[tuple[float, int]]:
    """Non-overlapping theoretical trades: (pnl, exit_bar)."""
    results: list[tuple[float, int]] = []
    last_exit = -1
    for sig in sorted(signals, key=lambda s: s.bar_idx):
        if sig.bar_idx <= last_exit:
            continue
        pnl, _, exit_bar = fast_theoretical_outcome(df, sig)
        results.append((pnl, exit_bar))
        last_exit = exit_bar
    return results
