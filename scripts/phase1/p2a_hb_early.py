"""P2-A: H-B EARLY + H-M5 + H-M4 Phase1-style verification."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_b_ignite import generate_hb_signals


def _monthly_n_hb(df, cooldown: int, mode: str = "early") -> float:
    sigs = generate_hb_signals(df, mode=mode, weekend_filter=True, cooldown=cooldown)
    trades = run_backtest(df, sigs, apply_execution=True)
    stats = summarize_trades(trades, df, "executed_pnl")
    return stats.get("monthly_n") or 0.0


def find_hb_cooldown(df, target_n: int = 50, mode: str = "early") -> int:
    lo, hi = 12, 576
    best_cd, best_dist = 48, float("inf")
    for cd in range(lo, hi + 1, 12):
        mn = _monthly_n_hb(df, cd, mode=mode)
        dist = abs(mn - target_n)
        if dist < best_dist:
            best_dist, best_cd = dist, cd
    return best_cd


def _run_split(df, split: str, cooldown: int, rr_ratio: float = 2.0) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hb_signals(
        sub,
        mode="early",
        weekend_filter=True,
        late_entry_ban=True,
        cooldown=cooldown,
        pct_risk=0.010,
        rr_ratio=rr_ratio,
        max_bars=48,
    )
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    sl, tp = 0.010, 0.010 * rr_ratio
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, 48)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["cooldown"] = cooldown
    m["rr_ratio"] = rr_ratio
    return m


def compute(df) -> dict[str, dict]:
    all_df = filter_df_by_split(df, "ALL")
    cooldown = find_hb_cooldown(all_df, target_n=50, mode="early")

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P2-HB-EARLY_{split}"] = _run_split(df, split, cooldown, rr_ratio=2.0)

    # RR 1:3 OOS emphasis
    for split in ("OOS1", "OOS2"):
        m = _run_split(df, split, cooldown, rr_ratio=3.0)
        m["notes"] = "RR 1:3"
        metrics[f"P2-HB-EARLY-RR3_{split}"] = m

    metrics["P2-HB-EARLY_M4"] = _run_split(df, "ALL", cooldown, rr_ratio=2.0)
    metrics["P2-HB-EARLY_M4"]["weekend_filter"] = True
    metrics["P2-HB-EARLY_M4"]["cooldown_tuned"] = cooldown
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P2-HB-EARLY_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    return "reject"
