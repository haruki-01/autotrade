"""P2-C: H-B + H-D composite with H-M4."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.p2a_hb_early import find_hb_cooldown
from scripts.phase1.signals.h_b_ignite import generate_hb_signals
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals


def _composite_signals(df, cooldown_hb: int, cooldown_hd: int = 48):
    sigs = []
    sigs.extend(
        generate_hb_signals(
            df,
            mode="early",
            weekend_filter=True,
            late_entry_ban=True,
            cooldown=cooldown_hb,
            pct_risk=0.010,
            rr_ratio=2.0,
        )
    )
    sigs.extend(generate_hd_pull_signals(df, weekend_filter=True, mode="pull", cooldown=cooldown_hd))
    by_bar: dict = {}
    for s in sigs:
        prev = by_bar.get(s.bar_idx)
        if prev is None or "hb_" in s.tag:
            by_bar[s.bar_idx] = s
    return sorted(by_bar.values(), key=lambda x: x.bar_idx)


def _run_split(df, split: str, cooldown_hb: int) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = _composite_signals(sub, cooldown_hb)
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, 0.008, 0.016, 48)
    fee_be = fee_breakeven_win_rate(0.008, 0.016)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["components"] = {"hb_early": True, "hd_pull": True}
    return m


def compute(df) -> dict[str, dict]:
    all_df = filter_df_by_split(df, "ALL")
    cooldown_hb = find_hb_cooldown(all_df, target_n=25, mode="early")

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P2-HBD-COMPOSITE_{split}"] = _run_split(df, split, cooldown_hb)
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P2-HBD-COMPOSITE_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    return "reject"
