"""B03 Phase0: IGNITE early vs late."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    detect_ignite,
    ignite_edge,
    metric_from_series,
    months_in_sample,
    summarize_returns,
)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    df = detect_ignite(df)
    ignite_idx = df.index[df["is_ignite"]]
    early = ignite_edge(df, ignite_idx, "fwd_ret_48")

    late_indices = []
    pull_indices = []
    for idx in ignite_idx:
        i = df.index.get_loc(idx)
        start_price = df["close"].iloc[i - 2] if i >= 2 else df["close"].iloc[i]
        direction = int(df["ignite_dir"].iloc[i])
        window = df.iloc[i + 1 : i + 1 + 48]
        peak = start_price
        late_idx = None
        pull_idx = None
        for j, (_, row) in enumerate(window.iterrows()):
            if direction == 1:
                peak = max(peak, row["high"])
                move = (peak - start_price) / start_price
                if move >= 0.015 and late_idx is None:
                    late_idx = row.name
                if move >= 0.005 and pull_idx is None:
                    retrace = (peak - row["close"]) / max(peak - start_price, 1)
                    if 0.2 <= retrace <= 0.4:
                        pull_idx = row.name
            else:
                peak = min(peak, row["low"])
                move = (start_price - peak) / start_price
                if move >= 0.015 and late_idx is None:
                    late_idx = row.name
                if move >= 0.005 and pull_idx is None:
                    retrace = (row["close"] - peak) / max(start_price - peak, 1)
                    if 0.2 <= retrace <= 0.4:
                        pull_idx = row.name
        if late_idx is not None:
            late_indices.append(late_idx)
        if pull_idx is not None:
            pull_indices.append(pull_idx)

    late = ignite_edge(df, pd.Index(late_indices), "fwd_ret_48") if late_indices else pd.Series(dtype=float)
    pull = ignite_edge(df, pd.Index(pull_indices), "fwd_ret_48") if pull_indices else pd.Series(dtype=float)

    months = months_in_sample(df)
    freq = len(ignite_idx) / months
    vs = float(early.mean() - late.mean()) if len(early) and len(late) else np.nan

    high_body = df.loc[ignite_idx][df.loc[ignite_idx, "body"] >= df.loc[ignite_idx, "body_med100"] * 1.5].index
    low_body = df.loc[ignite_idx][df.loc[ignite_idx, "body"] < df.loc[ignite_idx, "body_med100"] * 1.5].index
    high_e = ignite_edge(df, high_body, "fwd_ret_48")
    low_e = ignite_edge(df, low_body, "fwd_ret_48")
    body_delta = float(high_e.mean() - low_e.mean()) if len(high_e) and len(low_e) else np.nan

    results = {
        "P0-HB-EARLY": metric_from_series(early, vs_baseline=vs, min_n=100, notes=f"vs LATE diff={vs}"),
        "P0-HB-LATE": metric_from_series(late, min_n=30, notes=f"late_n={len(late)}"),
        "P0-HB-PULL": metric_from_series(pull, min_n=50, notes=f"pull_n={len(pull)}"),
        "P0-HB-FREQ": {
            "n": int(len(ignite_idx)),
            "hit_rate": np.nan,
            "mean_edge": freq,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "pass" if 3 <= freq <= 15 else "weak",
            "notes": f"ignites/month={freq:.1f}",
        },
        "P0-HB-BODY": {
            "n": int(len(ignite_idx)),
            "mean_edge": body_delta,
            "hit_rate": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": body_delta,
            "verdict": "weak",
            "notes": f"high_body_mean={high_e.mean() if len(high_e) else np.nan}",
        },
        "P0-HB5-SPLIT": {
            "n": int(len(ignite_idx)),
            "mean_edge": body_delta,
            "hit_rate": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": body_delta,
            "verdict": "weak" if body_delta and body_delta > 0 else "fail",
            "notes": "high vs low body ignite",
        },
    }
    if vs and vs > 0.0001:
        results["P0-HB-EARLY"]["verdict"] = "pass"
    return results


def batch_verdict(results: dict[str, dict]) -> str:
    early = results.get("P0-HB-EARLY", {})
    late = results.get("P0-HB-LATE", {})
    freq = results.get("P0-HB-FREQ", {}).get("mean_edge", 0)
    if early.get("mean_edge", 0) > (late.get("mean_edge") or 0) and early.get("n", 0) >= 100:
        if 3 <= freq <= 15:
            return "promote"
        return "conditional"
    if early.get("verdict") in ("pass", "weak"):
        return "conditional"
    return "reject"
