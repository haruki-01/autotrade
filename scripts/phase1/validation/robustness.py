"""Robustness stress tests: fee/slip degradation."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable

import numpy as np
import pandas as pd

from scripts.phase1 import common as common_mod
from scripts.phase1.backtest import run_backtest
from scripts.phase1.validation.risk_metrics import extended_summarize, profit_factor


@contextmanager
def _stress(fee_mult: float = 1.0, slip_mult: float = 1.0):
    orig_slip = common_mod.MARKET_SLIP
    orig_trade = common_mod.TRADE_FEE
    common_mod.MARKET_SLIP = orig_slip * slip_mult
    common_mod.TRADE_FEE = orig_trade * fee_mult
    try:
        yield
    finally:
        common_mod.MARKET_SLIP = orig_slip
        common_mod.TRADE_FEE = orig_trade


def run_robustness(
    df: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], list],
    *,
    fee_stress: float = 1.2,
    slip_stress: float = 1.2,
) -> dict:
    baseline_trades = run_backtest(df, signal_fn(df), apply_execution=True)
    baseline_pnls = [t.executed_pnl for t in baseline_trades if t.filled]
    baseline_pf = profit_factor(baseline_pnls)
    baseline_stats = extended_summarize(baseline_trades, df, "executed_pnl")

    scenarios = {}
    for name, fm, sm in [
        ("baseline", 1.0, 1.0),
        ("fee_plus_20pct", fee_stress, 1.0),
        ("slip_plus_20pct", 1.0, slip_stress),
        ("fee_slip_plus_20pct", fee_stress, slip_stress),
    ]:
        with _stress(fm, sm):
            trades = run_backtest(df, signal_fn(df), apply_execution=True)
            stats = extended_summarize(trades, df, "executed_pnl")
            pnls = [t.executed_pnl for t in trades if t.filled]
            scenarios[name] = {
                "ev": stats.get("ev"),
                "p": stats.get("p"),
                "profit_factor": profit_factor(pnls),
                "max_dd": stats.get("max_dd"),
            }

    stressed_pf = scenarios.get("fee_slip_plus_20pct", {}).get("profit_factor") or 0
    baseline_pf_val = baseline_pf if not np.isinf(baseline_pf) else 999.0
    return {
        "baseline": baseline_stats,
        "scenarios": scenarios,
        "pass": bool(stressed_pf >= 1.0 or (baseline_pf_val >= 1.15 and (scenarios["fee_plus_20pct"]["profit_factor"] or 0) >= 1.0)),
    }
