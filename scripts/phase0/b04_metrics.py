"""B04 Phase0: SQUEEZE_RELEASE and SWING_CHAIN."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, metric_from_series, months_in_sample


def detect_squeeze_release(df: pd.DataFrame) -> pd.Index:
    rv = df["rv_20"]
    threshold = rv.rolling(500, min_periods=100).quantile(0.2)
    compressed = rv <= threshold
    idx_list = []
    run = 0
    for i in range(len(df)):
        if compressed.iloc[i]:
            run += 1
        else:
            if run >= 12 and i < len(df):
                bar = df.iloc[i]
                comp_range = df.iloc[i - run : i]["range"].median()
                if bar["range"] >= comp_range * 2 and bar["body"] > 0:
                    direction = 1 if bar["close"] > bar["open"] else -1
                    idx_list.append((df.index[i], direction))
            run = 0
    return pd.Index([x[0] for x in idx_list])


def detect_swing_chain(df: pd.DataFrame) -> pd.Index:
    """Two consecutive swing high/low updates in same direction."""
    window = 6
    highs = df["high"].values
    lows = df["low"].values
    chain_idx = []
    last_swing_high = last_swing_low = np.nan
    swing_high_count = swing_low_count = 0
    for i in range(window, len(df) - window):
        h = highs[i]
        l = lows[i]
        is_swing_high = h == highs[i - window : i + window + 1].max()
        is_swing_low = l == lows[i - window : i + window + 1].min()
        if is_swing_high and h > last_swing_high:
            swing_high_count += 1
            last_swing_high = h
            if swing_high_count == 2:
                chain_idx.append(df.index[i])
        elif is_swing_high:
            swing_high_count = 1
            last_swing_high = h
        if is_swing_low and l < last_swing_low:
            swing_low_count += 1
            last_swing_low = l
            if swing_low_count == 2:
                chain_idx.append(df.index[i])
        elif is_swing_low:
            swing_low_count = 1
            last_swing_low = l
    return pd.Index(chain_idx)


def squeeze_edges(df: pd.DataFrame, indices: pd.Index, col: str = "fwd_ret_48") -> pd.Series:
    edges = []
    for idx in indices:
        i = df.index.get_loc(idx)
        bar = df.iloc[i]
        d = 1 if bar["close"] > bar["open"] else -1
        fwd = df[col].iloc[i]
        if not np.isnan(fwd):
            edges.append(d * fwd)
    return pd.Series(edges)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    sq_idx = detect_squeeze_release(df)
    sq_edge = squeeze_edges(df, sq_idx)

    fake = 0
    for idx in sq_idx:
        i = df.index.get_loc(idx)
        if i + 6 >= len(df):
            continue
        d = 1 if df["close"].iloc[i] > df["open"].iloc[i] else -1
        mid = (df["high"].iloc[i - 12 : i].max() + df["low"].iloc[i - 12 : i].min()) / 2
        rev = df["close"].iloc[i + 6]
        if (d == 1 and rev < mid) or (d == -1 and rev > mid):
            fake += 1
    fake_rate = fake / len(sq_idx) if len(sq_idx) else np.nan

    sw_idx = detect_swing_chain(df)
    sw_edge = squeeze_edges(df, sw_idx)
    third = 0
    for idx in sw_idx:
        i = df.index.get_loc(idx)
        if i + 48 < len(df):
            d = 1 if df["close"].iloc[i] > df["open"].iloc[i] else -1
            if d == 1 and df["high"].iloc[i + 48] > df["high"].iloc[i]:
                third += 1
            elif d == -1 and df["low"].iloc[i + 48] < df["low"].iloc[i]:
                third += 1
    months = months_in_sample(df)

    return {
        "P0-HB2-DIR": metric_from_series(sq_edge, min_n=50, notes=f"squeeze_n={len(sq_idx)}"),
        "P0-HB2-FAKE": {
            "n": len(sq_idx),
            "hit_rate": fake_rate,
            "mean_edge": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "pass" if fake_rate and fake_rate < 0.5 else "weak",
            "notes": f"fake_rate={fake_rate}",
        },
        "P0-HB2-FREQ": {
            "n": len(sq_idx),
            "mean_edge": len(sq_idx) / months,
            "hit_rate": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "weak",
            "notes": f"per_month={len(sq_idx)/months:.1f}",
        },
        "P0-HB3-CONT": metric_from_series(sw_edge, min_n=50, notes=f"swing_chain_n={len(sw_idx)}"),
        "P0-HB3-3RD": {
            "n": len(sw_idx),
            "hit_rate": third / len(sw_idx) if len(sw_idx) else np.nan,
            "mean_edge": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "weak",
            "notes": f"third_reach={third}/{len(sw_idx)}",
        },
    }


def batch_verdict(results: dict[str, dict]) -> str:
    if results.get("P0-HB2-DIR", {}).get("verdict") == "pass":
        return "conditional"
    if results.get("P0-HB3-CONT", {}).get("mean_edge", 0) > 0:
        return "conditional"
    return "reject"
