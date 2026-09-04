"""P2-B: H-B PULL entry + H-M5 + H-M4."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.p2a_hb_early import find_hb_cooldown
from scripts.phase1.signals.h_b_ignite import generate_hb_signals


def _run_split(df, split: str, cooldown: int, mode: str = "pull") -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hb_signals(
        sub,
        mode=mode,
        weekend_filter=True,
        late_entry_ban=True,
        cooldown=cooldown,
        pct_risk=0.010,
        rr_ratio=2.0,
        max_bars=48,
    )
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    sl, tp = 0.010, 0.020
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, 48)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["mode"] = mode
    return m


def compute(df) -> dict[str, dict]:
    all_df = filter_df_by_split(df, "ALL")
    cooldown = find_hb_cooldown(all_df, target_n=50, mode="pull")

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P2-HB-PULL_{split}"] = _run_split(df, split, cooldown, mode="pull")

    metrics["P2-HB-LATE-CTRL"] = _run_split(df, "ALL", cooldown, mode="late")
    metrics["P2-HB-LATE-CTRL"]["verdict"] = "reference"
    metrics["P2-HB-LATE-CTRL"]["notes"] = "late entry control (+1.5%)"
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P2-HB-PULL_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    return "reject"
