"""P1-C: Composite Phase1 batch (gate-gated)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, pack_metric, random_baseline_w, summarize_trades
from scripts.phase1.signals.h_a2_spike import generate_ha2_signals
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "phase1"


def _gate1_passed() -> tuple[bool, bool]:
    hd_pass = ha2_pass = False
    p1a = OUT_DIR / "p1a_results.json"
    p1b = OUT_DIR / "p1b_results.json"
    if p1a.exists():
        d = json.loads(p1a.read_text())
        m = d.get("metrics", {})
        if m.get("P1-HD-PULL_M4", {}).get("gate1"):
            hd_pass = True
        else:
            for k, v in m.items():
                if "PULL" in k and v.get("gate1"):
                    hd_pass = True
    if p1b.exists():
        d = json.loads(p1b.read_text())
        for k, v in d.get("metrics", {}).items():
            if "HA2" in k and v.get("gate1"):
                ha2_pass = True
    return hd_pass, ha2_pass


def _composite_signals(df, use_hd: bool, use_ha2: bool):
    sigs = []
    if use_ha2:
        sigs.extend(generate_ha2_signals(df, weekend_filter=True, mode="cont"))
    if use_hd:
        sigs.extend(generate_hd_pull_signals(df, weekend_filter=True, mode="pull"))
    # SPIKE priority: ha2 tags sort first by bar, dedupe same bar keeping ha2
    by_bar: dict = {}
    for s in sigs:
        prev = by_bar.get(s.bar_idx)
        if prev is None or "ha2" in s.tag:
            by_bar[s.bar_idx] = s
    return sorted(by_bar.values(), key=lambda x: x.bar_idx)


def _run_split(df, split: str, use_hd: bool, use_ha2: bool) -> dict:
    sub = filter_df_by_split(df, split)
    sigs = _composite_signals(sub, use_hd, use_ha2)
    th = run_backtest(sub, sigs, apply_execution=False)
    ex = run_backtest(sub, sigs, apply_execution=True)
    stats_th = summarize_trades(th, sub, "theoretical_pnl")
    stats_ex = summarize_trades(ex, sub, "executed_pnl")
    rand_w = random_baseline_w(sub, stats_th.get("n") or 0, 1, 0.008, 0.016, 48)
    fee_be = fee_breakeven_win_rate(0.008, 0.016)
    m = pack_metric(stats_th, stats_ex, rand_w, fee_be)
    m["split"] = split
    m["components"] = {"hd": use_hd, "ha2": use_ha2}
    return m


def compute(df) -> dict[str, dict]:
    hd_pass, ha2_pass = _gate1_passed()
    if not hd_pass and not ha2_pass:
        return {
            "P1-COMPOSITE_SKIPPED": {
                "verdict": "skipped",
                "notes": "Neither P1-A nor P1-B passed Gate1",
            }
        }

    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P1-COMPOSITE_{split}"] = _run_split(df, split, use_hd=hd_pass, use_ha2=ha2_pass)
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    if results.get("P1-COMPOSITE_SKIPPED"):
        return "defer"
    oos = [results.get(f"P1-COMPOSITE_{s}", {}) for s in ("OOS1", "OOS2")]
    if any(m.get("gate2") for m in oos):
        return "promote"
    if any(m.get("gate1") for m in oos):
        return "conditional"
    return "reject"
