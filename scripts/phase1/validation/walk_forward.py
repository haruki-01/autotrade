"""Walk-forward validation windows."""

from __future__ import annotations

from datetime import date
from typing import Callable

import numpy as np
import pandas as pd

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import Trade
from scripts.phase1.validation.risk_metrics import extended_summarize, profit_factor

# (train_start, train_end, test_start, test_end)
WALK_FORWARD_WINDOWS: list[tuple[date, date, date, date]] = [
    (date(2024, 1, 1), date(2025, 6, 30), date(2025, 7, 1), date(2026, 2, 28)),
    (date(2024, 1, 1), date(2025, 12, 31), date(2026, 1, 1), date(2026, 8, 31)),
    (date(2024, 7, 1), date(2025, 12, 31), date(2026, 1, 1), date(2026, 8, 31)),
]


def _filter_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    ts_start = pd.Timestamp(start, tz=df["open_time"].dt.tz)
    ts_end = pd.Timestamp(end, tz=df["open_time"].dt.tz) + pd.Timedelta(hours=23, minutes=55)
    mask = (df["open_time"] >= ts_start) & (df["open_time"] <= ts_end)
    return df.loc[mask].reset_index(drop=True)


def run_walk_forward(
    df: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], list],
    *,
    apply_execution: bool = True,
    windows: list | None = None,
) -> dict:
    windows = windows or WALK_FORWARD_WINDOWS
    results = []
    passes = 0

    for i, (ts, te, vs, ve) in enumerate(windows):
        test_df = _filter_range(df, vs, ve)
        if test_df.empty:
            continue
        sigs = signal_fn(test_df)
        trades: list[Trade] = run_backtest(test_df, sigs, apply_execution=apply_execution)
        stats = extended_summarize(trades, test_df, "executed_pnl" if apply_execution else "theoretical_pnl")
        ev = stats.get("ev") or 0
        pf = stats.get("profit_factor") or 0
        passed = ev > 0 and (pf >= 1.0 or np.isinf(pf))
        if passed:
            passes += 1
        results.append(
            {
                "window": i + 1,
                "train": f"{ts}..{te}",
                "test": f"{vs}..{ve}",
                "n": stats.get("n"),
                "ev": stats.get("ev"),
                "p": stats.get("p"),
                "profit_factor": stats.get("profit_factor"),
                "max_dd": stats.get("max_dd"),
                "pass": bool(passed),
            }
        )

    n_windows = len(results)
    pass_rate = passes / n_windows if n_windows else 0.0
    return {
        "windows": results,
        "n_windows": n_windows,
        "pass_count": passes,
        "pass_rate": pass_rate,
        "pass": pass_rate >= 0.60,
    }
