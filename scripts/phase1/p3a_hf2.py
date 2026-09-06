"""P3-A: H-F2 VOL_SHOCK midpoint reversion Phase1 batch."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_f2_volshock import (
    expected_monthly_events,
    generate_hf2_mid_signals,
)


def _monthly_n(df, cooldown: int, mode: str = "mid") -> float:
    sigs = generate_hf2_mid_signals(df, weekend_filter=True, cooldown=cooldown, mode=mode)
    trades = run_backtest(df, sigs, apply_execution=True)
    stats = summarize_trades(trades, df, "executed_pnl")
    return stats.get("monthly_n") or 0.0


def find_hf2_cooldown(df, target_n: int = 50, mode: str = "mid") -> int:
    lo, hi = 12, 576
    best_cd, best_dist = 48, float("inf")
    for cd in range(lo, hi + 1, 12):
        mn = _monthly_n(df, cd, mode=mode)
        dist = abs(mn - target_n)
        if dist < best_dist:
            best_dist, best_cd = dist, cd
    return best_cd


def _run_split(df, split: str, cooldown: int, mode: str = "mid", rr_ratio: float = 2.0) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hf2_mid_signals(
        sub,
        weekend_filter=True,
        cooldown=cooldown,
        mode=mode,
        pct_risk=0.010,
        rr_ratio=rr_ratio,
        max_bars=24,
    )
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    sl, tp = 0.010, 0.020
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, 24)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["mode"] = mode
    m["cooldown"] = cooldown
    m["rr_ratio"] = rr_ratio
    return m


def preflight(df, phase0_baseline: dict | None = None) -> list[dict]:
    from scripts.research.preflight import check_signal_count, check_sign_consistency

    all_df = filter_df_by_split(df, "ALL")
    mid_sigs = generate_hf2_mid_signals(all_df, weekend_filter=True, cooldown=48, mode="mid")
    exp_mo = expected_monthly_events(all_df)
    checks = [
        check_signal_count("hf2_mid", len(mid_sigs), min_count=50, expected_monthly=exp_mo),
    ]
    cont_sigs = generate_hf2_mid_signals(all_df, weekend_filter=True, cooldown=48, mode="cont")
    checks.append(
        {
            "name": "hf2_cont_ctrl",
            "ok": len(cont_sigs) >= 10,
            "level": "warn" if len(cont_sigs) < 10 else "info",
            "detail": f"control signals count={len(cont_sigs)}",
        }
    )
    if phase0_baseline:
        p0_mid = phase0_baseline.get("P0-HF2-MID", {}).get("mean_edge")
        th = _run_split(df, "ALL", 48, mode="mid")
        checks.append(check_sign_consistency("hf2_mid", p0_mid, th.get("theoretical_ev")))
    return checks


def compute(df) -> dict[str, dict]:
    all_df = filter_df_by_split(df, "ALL")
    cooldown = find_hf2_cooldown(all_df, target_n=50, mode="mid")

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P3-HF2-MID_{split}"] = _run_split(df, split, cooldown, mode="mid", rr_ratio=2.0)

    metrics["P3-HF2-CONT-CTRL"] = _run_split(df, "ALL", cooldown, mode="cont", rr_ratio=2.0)
    metrics["P3-HF2-CONT-CTRL"]["verdict"] = "reference"
    metrics["P3-HF2-M4"] = _run_split(df, "ALL", cooldown, mode="mid", rr_ratio=2.0)
    metrics["P3-HF2-M4"]["weekend_filter"] = True
    metrics["P3-HF2-M4"]["cooldown_tuned"] = cooldown
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P3-HF2-MID_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    return "reject"
