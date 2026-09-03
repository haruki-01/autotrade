"""Event-driven backtest runner for Phase1."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase1.common import Signal, Trade
from scripts.phase1.execution import simulate_trade


def run_backtest(df: pd.DataFrame, signals: list[Signal], apply_execution: bool = True, seed: int = 42) -> list[Trade]:
    rng = np.random.default_rng(seed)
    trades: list[Trade] = []
    last_exit = -1
    for sig in sorted(signals, key=lambda s: s.bar_idx):
        if sig.bar_idx <= last_exit:
            continue
        if sig.bar_idx >= len(df) - sig.max_bars - 1:
            continue
        trade = simulate_trade(df, sig, rng, apply_execution)
        if trade.filled:
            trades.append(trade)
            last_exit = trade.exit_bar_idx
    return trades


def signals_to_trades(df: pd.DataFrame, signals: list[Signal]) -> tuple[list[Trade], list[Trade]]:
    th = run_backtest(df, signals, apply_execution=False)
    ex = run_backtest(df, signals, apply_execution=True)
    return th, ex
