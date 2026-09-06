"""P1-R2: H-D fixed TP/SL exit grid on VALIDATION only (B10-driven)."""

from __future__ import annotations

from itertools import product

import numpy as np

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import evaluate_gates, fee_breakeven_win_rate, summarize_trades
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals
from scripts.phase1.validation.monte_carlo import run_monte_carlo
from scripts.phase1.validation.research_gate import evaluate_research_gate
from scripts.phase1.validation.risk_metrics import extended_summarize
from scripts.phase1.validation.robustness import run_robustness
from scripts.phase1.validation.walk_forward import run_walk_forward

TP_GRID = [0.005, 0.008, 0.010]
SL_GRID = [0.005, 0.008]
VALIDATION_SPLIT = "VALIDATION"


def _eval_combo(df, sl_pct: float, tp_pct: float) -> dict:
    sub = filter_df_by_split(df, VALIDATION_SPLIT)

    def signal_fn(d):
        return generate_hd_pull_signals(
            d, weekend_filter=True, mode="pull", sl_pct=sl_pct, tp_pct=tp_pct, max_bars=48, cooldown=48
        )

    sigs = signal_fn(sub)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats = extended_summarize(ex, sub, "executed_pnl")
    gate1, gate2 = evaluate_gates(stats)
    pnls = [t.executed_pnl for t in ex if t.filled]
    wf = run_walk_forward(df, signal_fn, apply_execution=True)
    mc = run_monte_carlo(pnls)
    robust = run_robustness(sub, signal_fn)
    stats["executed_ev"] = stats.get("ev")
    rg = evaluate_research_gate(stats, wf, mc, robust)
    fee_be = fee_breakeven_win_rate(sl_pct, tp_pct)
    return {
        "sl_pct": sl_pct,
        "tp_pct": tp_pct,
        "rr_effective": round(tp_pct / sl_pct, 2) if sl_pct else np.nan,
        "n": stats.get("n"),
        "w": stats.get("w"),
        "ev": stats.get("ev"),
        "p": stats.get("p"),
        "monthly_n": stats.get("monthly_n"),
        "max_dd": stats.get("max_dd"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "gate1": gate1,
        "gate2": gate2,
        "research_gate": rg.get("pass"),
        "wf_pass_rate": wf.get("pass_rate"),
        "fee_breakeven_w": fee_be,
        "w_check": (stats.get("w") or 0) >= fee_be,
    }


def compute(df) -> dict:
    grid = []
    for sl, tp in product(SL_GRID, TP_GRID):
        if tp <= sl:
            continue
        grid.append(_eval_combo(df, sl, tp))

    grid.sort(key=lambda x: (x.get("research_gate", False), x.get("p") or -1e9), reverse=True)
    best = grid[0] if grid else {}
    baseline = _eval_combo(df, 0.008, 0.016)  # RR 1:2 approx from P1-A

    return {
        "metrics": {
            "P1R2-BEST": {**best, "split": VALIDATION_SPLIT, "verdict": "pass" if best.get("gate2") else ("conditional" if best.get("gate1") else "fail")},
            "P1R2-BASELINE": {**baseline, "split": VALIDATION_SPLIT, "notes": "RR~1:2 pct=0.8/1.6"},
        },
        "grid": grid,
        "tuning_split": VALIDATION_SPLIT,
    }


def batch_verdict(results: dict) -> str:
    best = results.get("metrics", {}).get("P1R2-BEST", {})
    if best.get("gate2"):
        return "promote"
    if best.get("research_gate") or best.get("gate1"):
        return "conditional"
    baseline_p = results.get("metrics", {}).get("P1R2-BASELINE", {}).get("p") or 0
    best_p = best.get("p") or 0
    if best_p > baseline_p * 1.05:
        return "conditional"
    return "reject"
