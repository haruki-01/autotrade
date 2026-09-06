"""P1-L: Gate2 lever verification — H-D uplift, N-band EV, L1 filters."""

from __future__ import annotations

from itertools import product

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import (
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    filter_df_by_split,
)
from scripts.phase1.metrics import evaluate_gates, summarize_trades
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals

VALIDATION = "VALIDATION"
TEST = "TEST"
CANONICAL = {
    "weekend_filter": True,
    "mode": "pull",
    "sl_pct": HD_CANONICAL_SL_PCT,
    "tp_pct": HD_CANONICAL_TP_PCT,
}


def _eval(df, split: str, **sig_kw) -> dict:
    sub = filter_df_by_split(df, split)
    params = {**CANONICAL, **sig_kw}
    sigs = generate_hd_pull_signals(sub, **params)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats = summarize_trades(ex, sub, "executed_pnl")
    g1, g2 = evaluate_gates(stats)
    return {
        **params,
        "split": split,
        "executed_ev": stats.get("ev"),
        "n": stats.get("n"),
        "w": stats.get("w"),
        "monthly_n": stats.get("monthly_n"),
        "p": stats.get("p"),
        "max_dd": stats.get("max_dd"),
        "gate1": g1,
        "gate2": g2,
        "verdict": "pass" if g2 else ("conditional" if g1 else "fail"),
    }


def _confirm_test(df, val_best: dict) -> dict:
    keys = ("cooldown", "max_bars", "sl_pct", "tp_pct", "session_filter", "avoid_fee_window")
    sig_kw = {k: val_best[k] for k in keys if k in val_best and val_best[k] is not None}
    if "sl_pct" not in sig_kw:
        sig_kw.update({"sl_pct": HD_CANONICAL_SL_PCT, "tp_pct": HD_CANONICAL_TP_PCT})
    return _eval(df, TEST, **sig_kw)


def lever1_hd_uplift(df) -> dict:
    """Lever 1: cooldown × max_bars on canonical exit (VALIDATION tune)."""
    grid = []
    for cd, mb in product([24, 36, 48, 60, 72, 96], [36, 48, 72]):
        row = _eval(df, VALIDATION, cooldown=cd, max_bars=mb)
        row["lever"] = "L1-HD-uplift"
        grid.append(row)

    gate1_rows = [r for r in grid if r.get("gate1")]
    gate1_rows.sort(key=lambda x: (x.get("gate2", False), x.get("p") or -1e9), reverse=True)
    best = gate1_rows[0] if gate1_rows else max(grid, key=lambda x: x.get("p") or -1e9)
    test = _confirm_test(df, best) if best else {}

    return {
        "lever": "L1-HD-uplift",
        "question": "canonical H-D の cooldown/max_bars で P≥¥1,500（Gate2@3%）に届くか？",
        "grid_size": len(grid),
        "best_validation": best,
        "best_test": test,
        "gate2_val_count": sum(1 for r in grid if r.get("gate2")),
        "gate1_val_count": len(gate1_rows),
    }


def lever2_n_band(df) -> dict:
    """Lever 2: N帯内（Gate1）で exit/cooldown 探索."""
    grid = []
    for cd, sl, tp in product(
        [24, 36, 48, 60, 72, 84, 96],
        [0.004, 0.005, 0.006],
        [0.008, 0.010, 0.012],
    ):
        if tp <= sl:
            continue
        row = _eval(df, VALIDATION, cooldown=cd, max_bars=48, sl_pct=sl, tp_pct=tp)
        row["lever"] = "L2-N-band"
        if row.get("gate1"):
            grid.append(row)

    grid.sort(key=lambda x: (x.get("gate2", False), x.get("p") or -1e9), reverse=True)
    best = grid[0] if grid else {}
    test = _confirm_test(df, best) if best else {}

    return {
        "lever": "L2-N-band",
        "question": "Gate1 帯内で exit/cooldown 調整し Gate2@3% に届くか？",
        "grid_size": len(grid),
        "best_validation": best,
        "best_test": test,
        "gate2_val_count": sum(1 for r in grid if r.get("gate2")),
    }


def lever3_l1_filters(df) -> dict:
    """Lever 3: H-C session / H-E fee-window filters on canonical H-D."""
    configs = [
        {"label": "baseline", "session_filter": None, "avoid_fee_window": False},
        {"label": "TOKYO", "session_filter": "TOKYO", "avoid_fee_window": False},
        {"label": "EUROPE_US", "session_filter": "EUROPE_US", "avoid_fee_window": False},
        {"label": "OFF", "session_filter": "OFF", "avoid_fee_window": False},
        {"label": "avoid_fee_window", "session_filter": None, "avoid_fee_window": True},
    ]
    grid = []
    for cfg in configs:
        label = cfg["label"]
        sig_kw = {k: v for k, v in cfg.items() if k != "label"}
        row = _eval(df, VALIDATION, cooldown=48, max_bars=48, **sig_kw)
        row["lever"] = "L3-L1-filter"
        row["filter_label"] = label
        grid.append(row)

    gate1_rows = [r for r in grid if r.get("gate1")]
    gate1_rows.sort(key=lambda x: (x.get("gate2", False), x.get("p") or -1e9), reverse=True)
    best = gate1_rows[0] if gate1_rows else {}
    test = _confirm_test(df, best) if best else {}

    return {
        "lever": "L3-L1-filter",
        "question": "H-C session / H-E fee 窓フィルタで H-D P 改善するか？",
        "grid": grid,
        "best_validation": best,
        "best_test": test,
        "gate2_val_count": sum(1 for r in grid if r.get("gate2")),
    }


def compute(df) -> dict:
    l1 = lever1_hd_uplift(df)
    l2 = lever2_n_band(df)
    l3 = lever3_l1_filters(df)

    p1r2c_p = 1030.88  # P1-R2C VALIDATION reference
    improvements = []
    for name, block in ("L1", l1), ("L2", l2), ("L3", l3):
        bv = block.get("best_validation") or {}
        if bv.get("p"):
            improvements.append((name, bv.get("p"), bv.get("gate2"), bv.get("gate1")))

    global_best = max(
        [l1, l2, l3],
        key=lambda b: ((b.get("best_validation") or {}).get("p") or -1e9),
    )
    gbv = global_best.get("best_validation") or {}
    gbt = global_best.get("best_test") or {}

    return {
        "metrics": {
            "P1L-L1-HD": {**l1["best_validation"], "lever": "L1", "test": l1["best_test"]},
            "P1L-L2-N": {**l2["best_validation"], "lever": "L2", "test": l2["best_test"]} if l2.get("best_validation") else {},
            "P1L-L3-FILTER": {**l3["best_validation"], "lever": "L3", "test": l3["best_test"]} if l3.get("best_validation") else {},
            "P1L-GLOBAL-BEST-VAL": gbv,
            "P1L-GLOBAL-BEST-TEST": gbt,
        },
        "levers": {"L1": l1, "L2": l2, "L3": l3},
        "p1r2c_validation_p": p1r2c_p,
        "improvement_vs_p1r2c_pct": round((gbv.get("p", 0) / p1r2c_p - 1) * 100, 1) if p1r2c_p else None,
        "tuning_split": VALIDATION,
    }


def batch_verdict(results: dict) -> str:
    levers = results.get("levers", {})
    for block in levers.values():
        test = block.get("best_test") or {}
        if test.get("gate2") and test.get("gate1"):
            return "promote"
    for block in levers.values():
        val = block.get("best_validation") or {}
        if val.get("gate2") and val.get("gate1"):
            return "conditional"
    imp = results.get("improvement_vs_p1r2c_pct") or 0
    if imp >= 5:
        return "conditional"
    return "reject"
