"""P1-N: N sensitivity grid (N=10,20,50,100) for H-D + H-M4."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import GATE2_P_TARGET, filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, summarize_trades
from scripts.phase1.n_targets import N_CANDIDATES, build_n_targets_table, n_band, w_for_ev
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals

OOS_SPLITS = ("OOS1", "OOS2")
COOLDOWN_SEARCH = (12, 576)


def _monthly_n_for_cooldown(df, cooldown: int) -> float:
    sigs = generate_hd_pull_signals(df, weekend_filter=True, mode="pull", cooldown=cooldown)
    trades = run_backtest(df, sigs, apply_execution=True)
    stats = summarize_trades(trades, df, "executed_pnl")
    return stats.get("monthly_n") or 0.0


def find_cooldown_for_n(df, n_target: int) -> int:
    lo, hi = COOLDOWN_SEARCH
    best_cd = lo
    best_dist = float("inf")
    while lo <= hi:
        mid = (lo + hi) // 2
        # Snap to 12-bar steps
        mid = max(12, (mid // 12) * 12)
        mn = _monthly_n_for_cooldown(df, mid)
        dist = abs(mn - n_target)
        if dist < best_dist:
            best_dist = dist
            best_cd = mid
        if mn > n_target:
            lo = mid + 12
        else:
            hi = mid - 12
    # Fine scan around best
    for cd in range(max(12, best_cd - 48), best_cd + 49, 12):
        mn = _monthly_n_for_cooldown(df, cd)
        dist = abs(mn - n_target)
        if dist < best_dist:
            best_dist = dist
            best_cd = cd
    return best_cd


def _evaluate_at_n(df, n_target: int, cooldown: int, target_row: dict) -> dict:
    band_low, band_high = n_band(n_target)
    split_stats = {}
    all_pnls = []

    for split in OOS_SPLITS:
        sub = filter_df_by_split(df, split)
        sigs = generate_hd_pull_signals(sub, weekend_filter=True, mode="pull", cooldown=cooldown)
        trades = run_backtest(sub, sigs, apply_execution=True)
        stats = summarize_trades(trades, sub, "executed_pnl")
        split_stats[split] = stats
        all_pnls.extend([t.executed_pnl for t in trades if t.filled])

    oos_ps = [split_stats[s]["p"] for s in OOS_SPLITS if split_stats[s].get("p") is not None]
    oos_avg_p = float(np.mean(oos_ps)) if oos_ps else np.nan
    oos_avg_n = float(np.mean([split_stats[s]["monthly_n"] for s in OOS_SPLITS]))
    oos_avg_ev = float(np.mean([split_stats[s]["ev"] for s in OOS_SPLITS if split_stats[s].get("ev") is not None]))
    oos_avg_w = float(np.mean([split_stats[s]["w"] for s in OOS_SPLITS if split_stats[s].get("w") is not None]))

    gate1 = oos_avg_ev > 0 and band_low <= oos_avg_n <= band_high
    gate2 = oos_avg_p >= GATE2_P_TARGET
    w_check = oos_avg_w >= target_row["w_star_gate2"] if not np.isnan(oos_avg_w) else False

    return {
        "n_target": n_target,
        "cooldown": cooldown,
        "n_band_low": band_low,
        "n_band_high": band_high,
        "ev_star_jpy": target_row["ev_star_jpy"],
        "w_star_gate2": target_row["w_star_gate2"],
        "fee_breakeven_w": target_row["fee_breakeven_w"],
        "oos_avg_ev": oos_avg_ev,
        "oos_avg_w": oos_avg_w,
        "oos_avg_n": oos_avg_n,
        "oos_avg_p": oos_avg_p,
        "gate1": gate1,
        "gate2": gate2,
        "w_check": w_check,
        "verdict": "pass" if gate2 else ("conditional" if gate1 else "fail"),
        "splits": split_stats,
    }


def compute(df) -> dict:
    # Use ALL for cooldown search (stable N estimate)
    all_df = filter_df_by_split(df, "ALL")
    targets = {r["n_target"]: r for r in build_n_targets_table()}
    metrics = {}
    for n in N_CANDIDATES:
        cd = find_cooldown_for_n(all_df, n)
        metrics[f"P1N-N{n}"] = _evaluate_at_n(df, n, cd, targets[n])
    return metrics


def batch_verdict(results: dict) -> str:
    if any(m.get("gate2") for m in results.values()):
        return "promote"
    if any(m.get("gate1") for m in results.values()):
        return "conditional"
    return "reject"
