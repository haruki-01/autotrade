"""B09 Phase0: H-F3 range-bound mean reversion."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    merge_htf,
    metric_from_series,
    months_in_sample,
    resample_ohlc,
)


def detect_range_bound_events(
    df: pd.DataFrame,
    range_quantile: float = 0.20,
    atr_touch_mult: float = 0.10,
    roll_bars: int = 24,
    quantile_window: int = 60,
) -> pd.DataFrame:
    """RANGE_BOUND: tight 12h range + 5m edge touch."""
    out = merge_htf(add_features(df))
    h12 = resample_ohlc(out, "12h")
    h12["range12"] = h12["high"] - h12["low"]
    h12["range12_pct"] = h12["range12"] / h12["close"]
    h12["range12_q"] = h12["range12_pct"].rolling(quantile_window, min_periods=20).quantile(range_quantile)

    out = pd.merge_asof(
        out.sort_values("open_time"),
        h12[["open_time", "range12", "range12_pct", "range12_q"]],
        on="open_time",
        direction="backward",
    )

    roll_high = out["high"].rolling(roll_bars, min_periods=roll_bars).max().shift(1)
    roll_low = out["low"].rolling(roll_bars, min_periods=roll_bars).min().shift(1)
    roll_mid = (roll_high + roll_low) / 2
    tight = out["range12_pct"] <= out["range12_q"]

    touch_upper = tight & (out["close"] >= roll_high - atr_touch_mult * out["atr14"])
    touch_lower = tight & (out["close"] <= roll_low + atr_touch_mult * out["atr14"])

    out["is_range_bound"] = touch_upper | touch_lower
    out["rb_dir"] = np.where(touch_upper, -1, np.where(touch_lower, 1, 0))  # revert direction
    out["rb_roll_mid"] = roll_mid
    out["rb_roll_high"] = roll_high
    out["rb_roll_low"] = roll_low
    return out


def _revert_edges(df: pd.DataFrame) -> pd.Series:
    sub = df.loc[df["is_range_bound"]]
    edges = []
    for idx in sub.index:
        row = df.loc[idx]
        d = int(row["rb_dir"])
        fwd = row["fwd_ret_24"]
        if np.isnan(fwd) or d == 0:
            continue
        edges.append(float(fwd if d == 1 else -fwd))
    return pd.Series(edges)


def _break_edges(df: pd.DataFrame) -> pd.Series:
    """Control: trade breakout direction at edge touch."""
    sub = df.loc[df["is_range_bound"]]
    edges = []
    for idx in sub.index:
        row = df.loc[idx]
        d = int(row["rb_dir"])
        fwd = row["fwd_ret_24"]
        if np.isnan(fwd) or d == 0:
            continue
        edges.append(float(-fwd if d == 1 else fwd))
    return pd.Series(edges)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = detect_range_bound_events(df)
    events = df.index[df["is_range_bound"]]
    revert = _revert_edges(df)
    brk = _break_edges(df)
    vs = float(revert.mean() - brk.mean()) if len(revert) and len(brk) else np.nan

    months = months_in_sample(df)
    freq = len(events) / months
    mean_abs = float(revert.abs().mean()) if len(revert) else np.nan

    edge_metric = metric_from_series(
        revert, vs_baseline=vs, min_n=50, notes=f"vs BREAK diff={vs:.6f}" if not np.isnan(vs) else ""
    )

    ev_verdict = "pass" if mean_abs >= 0.005 else ("weak" if mean_abs >= 0.002 else "fail")

    return {
        "P0-HF3-EDGE": edge_metric,
        "P0-HF3-BREAK": metric_from_series(brk, min_n=50, notes="breakout control at edge"),
        "P0-HF3-EV": {
            "n": int(len(revert)),
            "hit_rate": float((revert > 0).mean()) if len(revert) else np.nan,
            "mean_edge": mean_abs,
            "median_edge": float(revert.abs().median()) if len(revert) else np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": mean_abs,
            "vs_baseline": np.nan,
            "verdict": ev_verdict,
            "notes": f"mean|edge|={mean_abs:.4f}, target>=0.5% for Gate2 feasibility",
        },
        "P0-HF3-FREQ": {
            "n": int(len(events)),
            "hit_rate": np.nan,
            "mean_edge": freq,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "pass" if 10 <= freq <= 120 else "weak",
            "notes": f"events/month={freq:.1f}",
        },
    }


def batch_verdict(results: dict[str, dict]) -> str:
    edge = results.get("P0-HF3-EDGE", {})
    brk = results.get("P0-HF3-BREAK", {})
    ev = results.get("P0-HF3-EV", {})
    rev_mean = edge.get("mean_edge", 0) or 0
    brk_mean = brk.get("mean_edge", 0) or 0
    if edge.get("verdict") == "pass" and rev_mean > brk_mean:
        return "promote"
    if edge.get("verdict") in ("pass", "weak") and rev_mean > brk_mean and edge.get("n", 0) >= 50:
        return "conditional"
    if rev_mean > 0 and rev_mean > brk_mean:
        return "conditional"
    if ev.get("verdict") == "fail" and rev_mean <= 0:
        return "reject"
    return "reject"
