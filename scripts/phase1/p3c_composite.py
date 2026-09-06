"""P3-C: H-D filter + H-F3 composite Phase1 batch."""

from __future__ import annotations

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.p3bnr_eval import HF3NRConfig, _signal_kwargs
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals
from scripts.phase1.signals.h_f3_range import generate_hf3_revert_signals

DEFAULT_HF3 = HF3NRConfig(cooldown=4, range_quantile=0.40, atr_touch_mult=0.20)


def _build_hd_zones(df, lookback: int = 48) -> set[int]:
    """Bars within lookback after H-D RSI exit-OS trigger."""
    from scripts.phase0.b06_metrics import rsi_exit_os
    from scripts.phase0.common import add_features

    feat = add_features(df)
    zones: set[int] = set()
    for idx in rsi_exit_os(feat):
        t = feat.index.get_loc(idx)
        for b in range(t, min(t + lookback, len(feat))):
            zones.add(b)
    return zones


def generate_p3c_signals(df, hf3_cfg: HF3NRConfig | None = None, zone_lookback: int = 48):
    hf3_cfg = hf3_cfg or DEFAULT_HF3
    sig_kw = _signal_kwargs(hf3_cfg)
    hf3_sigs = generate_hf3_revert_signals(df, **sig_kw)
    zones = _build_hd_zones(df, lookback=zone_lookback)
    filtered = [s for s in hf3_sigs if s.bar_idx in zones]
    return filtered, len(hf3_sigs)


def _run_split(df, split: str, hf3_cfg: HF3NRConfig | None = None, zone_lookback: int = 48) -> dict:
    sub = filter_df_by_split(df, split)
    sigs, raw_n = generate_p3c_signals(sub, hf3_cfg, zone_lookback=zone_lookback)
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    cfg = hf3_cfg or DEFAULT_HF3
    sl, tp = cfg.pct_risk, cfg.pct_risk * cfg.rr_ratio
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, sl, tp, cfg.max_bars)
    fee_be = fee_breakeven_win_rate(sl, tp)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["hf3_raw_signals"] = raw_n
    m["filtered_signals"] = len(sigs)
    m["filter_ratio"] = len(sigs) / raw_n if raw_n else 0.0
    m["config"] = cfg.label()
    m["zone_lookback"] = zone_lookback
    return m


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P3C-COMPOSITE_{split}"] = _run_split(df, split)

    hf3_only = {}
    sig_kw = _signal_kwargs(DEFAULT_HF3)
    for split in ("OOS1", "OOS2"):
        sub = filter_df_by_split(df, split)
        sigs = generate_hf3_revert_signals(sub, **sig_kw)
        ex = run_backtest(sub, sigs, apply_execution=True)
        hf3_only[split] = summarize_trades(ex, sub, "executed_pnl")

    metrics["P3C-HF3-REF"] = {
        "notes": "H-F3 single reference (cd4_q40_at20)",
        "OOS1": hf3_only.get("OOS1"),
        "OOS2": hf3_only.get("OOS2"),
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    oos = [results.get(f"P3C-COMPOSITE_{s}", {}) for s in ("OOS1", "OOS2")]
    hf3_oos2 = results.get("P3C-HF3-REF", {}).get("OOS2", {})
    comp_oos2 = results.get("P3C-COMPOSITE_OOS2", {})

    if any(m.get("gate2") for m in oos):
        return "promote"
    if all(m.get("gate1") for m in oos):
        return "conditional"
    comp_ev = comp_oos2.get("executed_ev") or 0
    hf3_ev = hf3_oos2.get("ev") or 0
    if comp_ev > hf3_ev and comp_oos2.get("gate1"):
        return "conditional"
    if comp_ev > 0:
        return "conditional"
    return "reject"
