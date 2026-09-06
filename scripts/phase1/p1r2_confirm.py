"""P1-R2C: H-D canonical exit — fixed config on TRAIN/VALIDATION/TEST (no tuning)."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import (
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    filter_df_by_split,
)
from scripts.phase1.metrics import evaluate_gates, fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_d_pull import canonical_hd_kwargs, generate_hd_pull_signals
from scripts.phase1.validation.monte_carlo import run_monte_carlo
from scripts.phase1.validation.research_gate import evaluate_research_gate
from scripts.phase1.validation.risk_metrics import extended_summarize
from scripts.phase1.validation.robustness import run_robustness
from scripts.phase1.validation.walk_forward import run_walk_forward

SPLITS = ("TRAIN", "VALIDATION", "TEST")
FIXED_CONFIG = canonical_hd_kwargs()


def _signal_fn(df):
    return generate_hd_pull_signals(df, **FIXED_CONFIG)


def _run_split(df, split: str) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = _signal_fn(sub)
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    fee_be = fee_breakeven_win_rate(HD_CANONICAL_SL_PCT, HD_CANONICAL_TP_PCT)
    rand_w = random_baseline_w(
        sub,
        stats_th.get("n") or 0,
        1,
        HD_CANONICAL_SL_PCT,
        HD_CANONICAL_TP_PCT,
        FIXED_CONFIG["max_bars"],
    )
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    gate1, gate2 = evaluate_gates(stats_ex)
    m["split"] = split
    m["gate1"] = gate1
    m["gate2"] = gate2
    m["sl_pct"] = HD_CANONICAL_SL_PCT
    m["tp_pct"] = HD_CANONICAL_TP_PCT
    m["weekend_filter"] = True
    return m


def compute(df) -> dict:
    metrics = {}
    for split in SPLITS:
        metrics[f"P1R2C-HD_{split}"] = _run_split(df, split)

    val_df = filter_df_by_split(df, "VALIDATION")

    def val_signal_fn(d):
        return _signal_fn(d)

    ex = run_backtest(val_df, val_signal_fn(val_df), apply_execution=True)
    stats = extended_summarize(ex, val_df, "executed_pnl")
    stats["executed_ev"] = stats.get("ev")
    pnls = [t.executed_pnl for t in ex if t.filled]
    wf = run_walk_forward(df, val_signal_fn, apply_execution=True)
    mc = run_monte_carlo(pnls)
    robust = run_robustness(val_df, val_signal_fn)
    rg = evaluate_research_gate(stats, wf, mc, robust)
    metrics["P1R2C-RESEARCH-GATE"] = {
        "split": "VALIDATION",
        "research_gate": rg.get("pass"),
        "wf_pass_rate": wf.get("pass_rate"),
        "checks": rg.get("checks"),
        "notes": "Research Gate on VALIDATION only (config locked in P1-R2)",
    }

    return {
        "metrics": metrics,
        "fixed_config": {
            "sl_pct": HD_CANONICAL_SL_PCT,
            "tp_pct": HD_CANONICAL_TP_PCT,
            **{k: v for k, v in FIXED_CONFIG.items() if k not in ("sl_pct", "tp_pct")},
        },
        "tuning_split": "none (locked from P1-R2)",
    }


def batch_verdict(results: dict) -> str:
    metrics = results.get("metrics", {})
    val = metrics.get("P1R2C-HD_VALIDATION", {})
    test = metrics.get("P1R2C-HD_TEST", {})
    train = metrics.get("P1R2C-HD_TRAIN", {})

    if test.get("gate2"):
        return "promote"
    if val.get("gate1") and test.get("gate1"):
        return "conditional"
    if val.get("gate1") and (test.get("executed_ev") or 0) > 0:
        return "conditional"
    if (train.get("executed_ev") or 0) > 0 and val.get("gate1"):
        return "conditional"
    return "reject"
