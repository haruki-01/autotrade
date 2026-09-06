"""P2-F: H-D5 12h pin bar Phase1-style verification."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_d5_pin import expected_monthly_events, generate_hd5_signals, pin_12h_events


def preflight(df, phase0_baseline=None) -> list[dict]:
    all_df = filter_df_by_split(df, "ALL")
    events = pin_12h_events(all_df)
    monthly = expected_monthly_events(all_df)
    return [
        {
            "name": "hd5_pin_events",
            "ok": len(events) >= 30,
            "level": "error",
            "detail": f"pin_events={len(events)} (Phase0 n≈604)",
        },
        {
            "name": "hd5_monthly_n",
            "ok": True,
            "level": "info",
            "detail": f"monthly_events≈{monthly:.1f} (Gate1 band 40-60 unlikely)",
        },
    ]


def _run_split(
    df,
    split: str,
    mode: str = "fade",
    entry_mode: str = "pull",
    weekend_filter: bool = True,
) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = generate_hd5_signals(
        sub,
        mode=mode,
        entry_mode=entry_mode,
        weekend_filter=weekend_filter,
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
    m["entry_mode"] = entry_mode
    m["weekend_filter"] = weekend_filter
    m["expected_monthly_events"] = expected_monthly_events(sub)
    return m


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P2-HD5-FADE-PULL_{split}"] = _run_split(df, split, mode="fade", entry_mode="pull")
        metrics[f"P2-HD5-FADE-IMM_{split}"] = _run_split(df, split, mode="fade", entry_mode="immediate")
        metrics[f"P2-HD5-CONT-PULL_{split}"] = _run_split(df, split, mode="cont", entry_mode="pull")

    metrics["P2-HD5-FADE-PULL_M4"] = _run_split(df, "ALL", mode="fade", entry_mode="pull", weekend_filter=True)
    metrics["P2-HD5-META"] = {
        "pin_events_all": len(pin_12h_events(filter_df_by_split(df, "ALL"))),
        "expected_monthly_all": expected_monthly_events(filter_df_by_split(df, "ALL")),
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos_fade = [results.get(f"P2-HD5-FADE-PULL_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos_fade):
        return "promote"
    if any(m.get("gate1") for m in oos_fade):
        return "conditional"
    if all((m.get("executed_ev") or 0) > 0 for m in oos_fade if m.get("n")):
        return "conditional"
    return "reject"
