"""P2-D: H-B session-filtered (EU_US) + H-C exploration."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.p2a_hb_early import find_hb_cooldown
from scripts.phase1.signals.h_b_ignite import generate_hb_signals


def _run_split(df, split: str, session: str | None, cooldown: int) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hb_signals(
        sub,
        mode="early",
        weekend_filter=True,
        late_entry_ban=True,
        cooldown=cooldown,
        session_filter=session,
        pct_risk=0.010,
        rr_ratio=2.0,
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
    m["session"] = session or "ALL"
    return m


def compute(df) -> dict[str, dict]:
    all_df = filter_df_by_split(df, "ALL")
    cooldown = find_hb_cooldown(all_df, target_n=30, mode="early")

    metrics = {}
    for split in ("OOS1", "OOS2"):
        metrics[f"P2-HB-EU_{split}"] = _run_split(df, split, "EUROPE_US", cooldown)
        metrics[f"P2-HB-TOKYO_{split}"] = _run_split(df, split, "TOKYO", cooldown)
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos_eu = [results.get(f"P2-HB-EU_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos_eu):
        return "promote"
    if any(m.get("gate1") for m in oos_eu):
        return "conditional"
    return "reject"
