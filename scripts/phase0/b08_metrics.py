"""B08 Phase0: H-F2 vol shock mean reversion."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    detect_vol_shock,
    metric_from_series,
    months_in_sample,
)


def _mid_revert_edges(df: pd.DataFrame, shock_idx: pd.Index) -> pd.Series:
    edges: list[float] = []
    for idx in shock_idx:
        row = df.loc[idx]
        mid = (row["high"] + row["low"]) / 2
        close = row["close"]
        fwd = row["fwd_ret_24"]
        if np.isnan(fwd):
            continue
        if close > mid:
            edges.append(float(-fwd))
        elif close < mid:
            edges.append(float(fwd))
    return pd.Series(edges)


def _absrev_edges(df: pd.DataFrame, shock_idx: pd.Index) -> pd.Series:
    """Positive edge when forward 24-bar range shrinks vs shock bar range."""
    edges: list[float] = []
    for idx in shock_idx:
        i = df.index.get_loc(idx)
        if i + 24 >= len(df):
            continue
        shock_range = float(df["range"].iloc[i])
        fwd_range = float(df.iloc[i + 1 : i + 25]["range"].mean())
        close = float(df["close"].iloc[i])
        if close <= 0:
            continue
        edges.append((shock_range - fwd_range) / close)
    return pd.Series(edges)


def _cont_edges(df: pd.DataFrame, shock_idx: pd.Index) -> pd.Series:
    edges: list[float] = []
    for idx in shock_idx:
        row = df.loc[idx]
        fwd = row["fwd_ret_24"]
        direction = int(row["shock_dir"])
        if np.isnan(fwd) or direction == 0:
            continue
        edges.append(float(fwd if direction == 1 else -fwd))
    return pd.Series(edges)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    df = detect_vol_shock(df)
    shock_idx = df.index[df["is_vol_shock"]]

    mid = _mid_revert_edges(df, shock_idx)
    absrev = _absrev_edges(df, shock_idx)
    cont = _cont_edges(df, shock_idx)
    vs = float(mid.mean() - cont.mean()) if len(mid) and len(cont) else np.nan

    months = months_in_sample(df)
    freq = len(shock_idx) / months

    return {
        "P0-HF2-MID": metric_from_series(
            mid, vs_baseline=vs, min_n=50, notes=f"vs CONT diff={vs:.6f}" if not np.isnan(vs) else "vs CONT"
        ),
        "P0-HF2-ABSREV": metric_from_series(absrev, min_n=50, notes="vol contraction after shock"),
        "P0-HF2-CONT": metric_from_series(cont, min_n=50, notes="shock continuation control"),
        "P0-HF2-FREQ": {
            "n": int(len(shock_idx)),
            "hit_rate": np.nan,
            "mean_edge": freq,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "pass" if 3 <= freq <= 80 else "weak",
            "notes": f"shocks/month={freq:.1f}",
        },
    }


def batch_verdict(results: dict[str, dict]) -> str:
    mid = results.get("P0-HF2-MID", {})
    cont = results.get("P0-HF2-CONT", {})
    freq = results.get("P0-HF2-FREQ", {}).get("mean_edge", 0)
    mid_edge = mid.get("mean_edge", 0) or 0
    cont_edge = cont.get("mean_edge", 0) or 0
    if mid.get("verdict") == "pass" and mid_edge > cont_edge:
        return "promote"
    if mid.get("verdict") in ("pass", "weak") and mid_edge > cont_edge and mid.get("n", 0) >= 50:
        if 3 <= freq <= 80:
            return "conditional"
        return "conditional"
    if mid.get("verdict") == "weak" and mid_edge > 0:
        return "conditional"
    return "reject"
