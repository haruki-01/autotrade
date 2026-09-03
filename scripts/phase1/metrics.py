"""Phase1 aggregate metrics and gate evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import (
    GATE2_P_TARGET,
    N_BAND_HIGH,
    N_BAND_LOW,
    POSITION_Q,
    RANDOM_SEED,
    RANDOM_TRIALS,
    RR_RATIO,
    Signal,
    Trade,
    months_in_df,
)
from scripts.phase1.execution import simulate_trade


def _max_dd(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    equity = np.cumsum(pnls)
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    return float(dd.max()) if len(dd) else 0.0


def summarize_trades(trades: list[Trade], df: pd.DataFrame, pnl_attr: str = "executed_pnl") -> dict:
    pnls = [getattr(t, pnl_attr) for t in trades if t.filled]
    if not pnls:
        return {
            "n": 0,
            "w": np.nan,
            "ev": np.nan,
            "monthly_n": np.nan,
            "p": np.nan,
            "max_dd": np.nan,
        }
    months = months_in_df(df)
    n = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    ev = float(np.mean(pnls))
    monthly_n = n / months
    return {
        "n": n,
        "w": wins / n,
        "ev": ev,
        "monthly_n": monthly_n,
        "p": ev * monthly_n,
        "max_dd": _max_dd(pnls),
    }


def fee_breakeven_win_rate(sl_pct: float, tp_pct: float, cost_pct: float = 0.0004) -> float:
    """RR 1:2 breakeven W given proportional SL/TP and round-trip cost."""
    loss = sl_pct + cost_pct
    win = tp_pct - cost_pct
    if win + loss <= 0:
        return np.nan
    return loss / (loss + win)


def random_baseline_w(
    df: pd.DataFrame,
    n_trades: int,
    direction: int,
    sl_pct: float,
    tp_pct: float,
    max_bars: int,
    seed: int = RANDOM_SEED,
) -> float:
    if n_trades <= 0 or len(df) < max_bars + 10:
        return np.nan
    sample_n = min(n_trades, 80)
    rng = np.random.default_rng(seed)
    wins = []
    hi = len(df) - max_bars - 2
    for _ in range(RANDOM_TRIALS):
        trial_wins = 0
        for _ in range(sample_n):
            i = int(rng.integers(10, hi))
            entry = df["close"].iloc[i]
            sl = entry * (1 - sl_pct) if direction == 1 else entry * (1 + sl_pct)
            tp = entry * (1 + tp_pct) if direction == 1 else entry * (1 - tp_pct)
            sig = Signal(i, direction, entry, sl, tp, max_bars, tag="random")
            t = simulate_trade(df, sig, rng, apply_execution=False)
            if t.filled and t.theoretical_pnl > 0:
                trial_wins += 1
        wins.append(trial_wins / sample_n if sample_n else 0)
    return float(np.mean(wins))


def evaluate_gates(stats: dict) -> tuple[bool, bool]:
    ev = stats.get("ev") or 0
    monthly_n = stats.get("monthly_n") or 0
    p = stats.get("p") or 0
    gate1 = ev > 0 and N_BAND_LOW <= monthly_n <= N_BAND_HIGH
    gate2 = p >= GATE2_P_TARGET
    return gate1, gate2


def pack_metric(stats_th: dict, stats_ex: dict, random_w: float, fee_be_w: float) -> dict:
    deg = stats_ex["ev"] / stats_th["ev"] if stats_th.get("ev") not in (None, 0, np.nan) and stats_ex.get("ev") is not None else np.nan
    gate1, gate2 = evaluate_gates(stats_ex)
    return {
        "theoretical_ev": stats_th.get("ev"),
        "executed_ev": stats_ex.get("ev"),
        "degradation": deg,
        "n": stats_ex.get("n"),
        "w": stats_ex.get("w"),
        "monthly_n": stats_ex.get("monthly_n"),
        "p": stats_ex.get("p"),
        "max_dd": stats_ex.get("max_dd"),
        "random_w": random_w,
        "fee_breakeven_w": fee_be_w,
        "gate1": gate1,
        "gate2": gate2,
        "verdict": "pass" if gate2 else ("conditional" if gate1 else "fail"),
    }
