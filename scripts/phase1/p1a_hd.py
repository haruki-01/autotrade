"""P1-A: H-D + PULL Phase1 batch."""

from __future__ import annotations

import numpy as np

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import SPLITS, filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals


def _run_split(df, split: str, weekend_filter: bool) -> dict:
    sub = filter_df_by_split(df, split)
    pull_sigs = generate_hd_pull_signals(sub, weekend_filter=weekend_filter, mode="pull")
    th = run_backtest(sub, pull_sigs, apply_execution=False)
    ex = run_backtest(sub, pull_sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, 0.008, 0.016, 48)
    fee_be = fee_breakeven_win_rate(0.008, 0.016)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["weekend_filter"] = weekend_filter
    return m


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P1-HD-PULL_{split}"] = _run_split(df, split, weekend_filter=False)

    all_df = filter_df_by_split(df, "ALL")
    raw_sigs = generate_hd_pull_signals(all_df, mode="raw")
    raw_ex = run_backtest(all_df, raw_sigs, apply_execution=True)
    raw_stats = summarize_trades(raw_ex, all_df, "executed_pnl")
    metrics["P1-HD-RAW-CTRL"] = {
        "split": "ALL",
        "executed_ev": raw_stats.get("ev"),
        "w": raw_stats.get("w"),
        "n": raw_stats.get("n"),
        "verdict": "fail",
        "notes": "RAW immediate entry control",
    }

    pull_all = _run_split(df, "ALL", weekend_filter=False)
    metrics["P1-HD-RANDOM"] = {
        "split": "ALL",
        "random_w": pull_all.get("random_w"),
        "w": pull_all.get("w"),
        "verdict": "reference",
        "notes": "strategy W vs random W",
    }

    metrics["P1-HD-PULL_M4"] = _run_split(df, "ALL", weekend_filter=True)
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P1-HD-PULL_{s}", {}) for s in ("OOS1", "OOS2")]
    m4 = results.get("P1-HD-PULL_M4", {})
    gate1_pass = sum(1 for m in oos if m.get("gate1")) >= 1 or m4.get("gate1")
    gate2_pass = any(m.get("gate2") for m in oos) or m4.get("gate2")
    if gate2_pass:
        return "promote"
    if gate1_pass:
        return "conditional"
    return "reject"
