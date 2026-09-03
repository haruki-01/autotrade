"""P1-B: H-A2 SPIKE continuation Phase1 batch."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_a2_spike import generate_ha2_signals


def _run_split(df, split: str, weekend_filter: bool = False) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_ha2_signals(sub, weekend_filter=weekend_filter, mode="cont")
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    atr_pct_sl, atr_pct_tp = 0.003, 0.006  # ~0.3/0.6 ATR typical as pct proxy
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, atr_pct_sl, atr_pct_tp, 12)
    fee_be = fee_breakeven_win_rate(atr_pct_sl, atr_pct_tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    return m


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P1-HA2-CONT_{split}"] = _run_split(df, split)

    all_df = filter_df_by_split(df, "ALL")
    rev_sigs = generate_ha2_signals(all_df, mode="revert")
    rev_ex = run_backtest(all_df, rev_sigs, apply_execution=True)
    rev_stats = summarize_trades(rev_ex, all_df, "executed_pnl")
    metrics["P1-HA-REVERT-CTRL"] = {
        "split": "ALL",
        "executed_ev": rev_stats.get("ev"),
        "w": rev_stats.get("w"),
        "n": rev_stats.get("n"),
        "verdict": "reference",
    }

    cont_all = _run_split(df, "ALL")
    metrics["P1-HA2-RANDOM"] = {
        "split": "ALL",
        "random_w": cont_all.get("random_w"),
        "w": cont_all.get("w"),
        "verdict": "reference",
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P1-HA2-CONT_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos) or results.get("P1-HA2-CONT_IS", {}).get("gate1"):
        return "conditional"
    return "reject"
