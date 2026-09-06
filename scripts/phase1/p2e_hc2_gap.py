"""P2-E: H-C2 weekly gap Phase1-style verification."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_c2_gap import expected_monthly_events, generate_hc2_signals
from scripts.phase0.b07_metrics import week_open_events


def preflight(df, phase0_baseline=None) -> list[dict]:
    all_df = filter_df_by_split(df, "ALL")
    gaps = week_open_events(all_df)
    monthly = expected_monthly_events(all_df)
    return [
        {
            "name": "hc2_weekly_dedup",
            "ok": len(gaps) < 500,
            "level": "error",
            "detail": f"weekly_events={len(gaps)} (expect ~130, not 40k)",
        },
        {
            "name": "hc2_monthly_n",
            "ok": True,
            "level": "info",
            "detail": f"monthly_events≈{monthly:.1f} (Gate1 band 40-60 unlikely)",
        },
    ]


def _run_split(
    df,
    split: str,
    mode: str = "cont",
    min_gap_pct: float = 0.0,
    min_gap_abs: float | None = None,
) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hc2_signals(
        sub,
        mode=mode,
        min_gap_pct=min_gap_pct,
        min_gap_abs=min_gap_abs,
    )
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    sl, tp = 0.005, 0.010
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, 48)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["mode"] = mode
    m["min_gap_pct"] = min_gap_pct
    if min_gap_abs is not None:
        m["min_gap_abs"] = min_gap_abs
    m["expected_monthly_events"] = expected_monthly_events(sub, min_gap_pct)
    return m


def _gap_p75_train(df) -> float:
    train = filter_df_by_split(df, "IS")
    gaps = week_open_events(train)
    if gaps.empty:
        return 0.0
    return float(gaps["gap_abs"].quantile(0.75))


def compute(df) -> dict[str, dict]:
    gap_p75 = _gap_p75_train(df)

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P2-HC2-CONT_{split}"] = _run_split(df, split, mode="cont")
        metrics[f"P2-HC2-REVERT_{split}"] = _run_split(df, split, mode="revert")

    # Gap-size filters (VALIDATION only — exploratory)
    for label, min_gap in (("GAP05", 0.005), ("GAP10", 0.010)):
        m = _run_split(df, "OOS1", mode="cont", min_gap_pct=min_gap)
        m["notes"] = f"min_gap={min_gap:.1%}"
        metrics[f"P2-HC2-CONT-{label}_OOS1"] = m

    if gap_p75 > 0:
        m = _run_split(df, "OOS1", mode="cont", min_gap_abs=gap_p75)
        m["notes"] = f"min_gap=p75_train={gap_p75:.4f}"
        metrics[f"P2-HC2-CONT-P75_OOS1"] = m

    metrics["P2-HC2-META"] = {
        "gap_p75_train": gap_p75,
        "weekly_events_all": len(week_open_events(filter_df_by_split(df, "ALL"))),
        "expected_monthly_all": expected_monthly_events(filter_df_by_split(df, "ALL")),
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos_cont = [results.get(f"P2-HC2-CONT_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos_cont):
        return "promote"
    if any(m.get("gate1") for m in oos_cont):
        return "conditional"
    # Rare-event hypothesis: positive executed EV on both OOS splits is worth noting
    if all((m.get("executed_ev") or 0) > 0 for m in oos_cont if m.get("n")):
        return "conditional"
    return "reject"
