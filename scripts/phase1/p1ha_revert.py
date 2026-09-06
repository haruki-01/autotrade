"""P1-HA: H-A SPIKE revert Phase1 (executed rules not yet validated)."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_a2_spike import generate_ha2_signals


def _run_split(df, split: str, weekend_filter: bool = True) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_ha2_signals(sub, weekend_filter=weekend_filter, mode="revert")
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    sl, tp = 0.003, 0.006
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, 12)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["mode"] = "revert"
    return m


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P1-HA-REVERT_{split}"] = _run_split(df, split)

    all_df = filter_df_by_split(df, "ALL")
    cont_sigs = generate_ha2_signals(all_df, mode="cont")
    cont_ex = run_backtest(all_df, cont_sigs, apply_execution=True)
    cont_stats = summarize_trades(cont_ex, all_df, "executed_pnl")
    metrics["P1-HA2-CONT-CTRL"] = {
        "split": "ALL",
        "executed_ev": cont_stats.get("ev"),
        "w": cont_stats.get("w"),
        "n": cont_stats.get("n"),
        "verdict": "reference",
        "notes": "H-A2 continuation control",
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P1-HA-REVERT_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    val = results.get("P1-HA-REVERT_OOS1", {})
    if (val.get("executed_ev") or 0) > 0:
        return "conditional"
    return "reject"
