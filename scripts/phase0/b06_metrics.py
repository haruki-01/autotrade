"""B06 Phase0: crowd / template bot signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, merge_htf, metric_from_series, months_in_sample, resample_ohlc


def rsi_exit_os(df: pd.DataFrame) -> pd.Index:
    idx = []
    was_os = False
    for i in range(len(df)):
        rsi = df["rsi14"].iloc[i]
        if np.isnan(rsi):
            continue
        if rsi <= 30:
            was_os = True
        elif was_os and rsi > 30:
            idx.append(df.index[i])
            was_os = False
    return pd.Index(idx)


def long_edge_after(df: pd.DataFrame, indices: pd.Index, col: str = "fwd_ret_48") -> pd.Series:
    return df.loc[indices, col].dropna()


def pull_after_rsi(df: pd.DataFrame, indices: pd.Index) -> pd.Series:
    edges = []
    for idx in indices:
        i = df.index.get_loc(idx)
        if i + 12 >= len(df):
            continue
        window = df.iloc[i + 1 : i + 13]
        if window.empty:
            continue
        pull_low = window["low"].min()
        entry_i = window["low"].idxmin()
        fwd = df.loc[entry_i, "fwd_ret_48"]
        if not np.isnan(fwd):
            edges.append(fwd)
    return pd.Series(edges)


def round_touch_indices(df: pd.DataFrame) -> pd.Index:
    idx = []
    for i in range(len(df)):
        price = df["close"].iloc[i]
        atr = df["atr14"].iloc[i]
        if np.isnan(atr):
            continue
        level = round(price / 100000) * 100000
        if abs(price - level) <= atr * 0.15:
            idx.append(df.index[i])
    return pd.Index(idx)


def ema_cross_1h(df: pd.DataFrame) -> pd.Index:
    h1 = resample_ohlc(df, "1h")
    h1["ema20"] = h1["close"].ewm(span=20, adjust=False).mean()
    h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
    h1["cross_up"] = (h1["ema20"] > h1["ema50"]) & (h1["ema20"].shift(1) <= h1["ema50"].shift(1))
    h1["cross_down"] = (h1["ema20"] < h1["ema50"]) & (h1["ema20"].shift(1) >= h1["ema50"].shift(1))
    times = h1.loc[h1["cross_up"] | h1["cross_down"], "open_time"]
    merged = pd.merge_asof(
        df[["open_time"]].sort_values("open_time"),
        times.to_frame("cross_time"),
        left_on="open_time",
        right_on="cross_time",
        direction="backward",
    )
    mask = merged["cross_time"].notna() & (merged["open_time"] - merged["cross_time"] < pd.Timedelta(hours=1))
    return df.loc[mask.values].index


def pct_level_events(df: pd.DataFrame, pct: float = -0.01) -> pd.Index:
    idx = []
    for i in range(24, len(df)):
        swing = df["high"].iloc[i - 24 : i].max()
        level = swing * (1 + pct)
        if df["low"].iloc[i] <= level <= df["high"].iloc[i]:
            idx.append(df.index[i])
    return pd.Index(idx)


def pin_12h_indices(df: pd.DataFrame) -> pd.Index:
    h12 = resample_ohlc(df, "12h")
    idx = []
    for _, bar in h12.iterrows():
        body = abs(bar["close"] - bar["open"])
        rng = bar["high"] - bar["low"]
        if rng == 0 or body == 0:
            continue
        upper = bar["high"] - max(bar["open"], bar["close"])
        lower = min(bar["open"], bar["close"]) - bar["low"]
        if upper >= 2 * body or lower >= 2 * body:
            t = bar["open_time"]
            match = df.loc[(df["open_time"] >= t) & (df["open_time"] < t + pd.Timedelta(hours=12))]
            if not match.empty:
                idx.append(match.index[-1])
    return pd.Index(idx)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    df = merge_htf(df)
    rsi_idx = rsi_exit_os(df)
    raw = long_edge_after(df, rsi_idx)
    pull = pull_after_rsi(df, rsi_idx)
    align_idx = [i for i in rsi_idx if df["h12_regime"].loc[i] == 1]
    align = long_edge_after(df, pd.Index(align_idx))

    rt = round_touch_indices(df)
    rt_fwd = long_edge_after(df, rt, "fwd_ret_12")
    mag = rt_fwd  # toward round simplified as forward
    reject = -rt_fwd
    through = long_edge_after(df, rt, "fwd_ret_48")

    cross_idx = ema_cross_1h(df)
    imm = long_edge_after(df, cross_idx)
    delay_idx = []
    for idx in cross_idx:
        i = df.index.get_loc(idx)
        if i + 6 < len(df):
            delay_idx.append(df.index[i + 6])
    delay = long_edge_after(df, pd.Index(delay_idx))

    bounce_idx = pct_level_events(df, -0.01)
    break_idx = pct_level_events(df, -0.015)
    bounce = -long_edge_after(df, bounce_idx, "fwd_ret_12")
    brk = long_edge_after(df, break_idx, "fwd_ret_12")

    pin_idx = pin_12h_indices(df)
    pin_fwd = long_edge_after(df, pin_idx, "fwd_ret_48")
    fade = -pin_fwd
    months = months_in_sample(df)

    return {
        "P0-HD-RAW": metric_from_series(raw, min_n=100, notes=f"n={len(raw)}"),
        "P0-HD-PULL": metric_from_series(pull, min_n=50, notes=f"pull>raw={pull.mean() > raw.mean() if len(pull) and len(raw) else 'na'}"),
        "P0-HD-ALIGN": metric_from_series(align, min_n=50, notes=f"12h aligned n={len(align)}"),
        "P0-HD-FREQ": {"n": len(rsi_idx), "mean_edge": len(rsi_idx) / months, "hit_rate": np.nan, "median_edge": np.nan, "p25": np.nan, "p75": np.nan, "mean_abs_move": np.nan, "vs_baseline": np.nan, "verdict": "weak", "notes": ""},
        "P0-HD2-MAG": metric_from_series(mag, min_n=50),
        "P0-HD2-REJECT": metric_from_series(reject, min_n=50),
        "P0-HD2-THROUGH": metric_from_series(through, min_n=50),
        "P0-HD3-IMMEDIATE": metric_from_series(imm, min_n=50),
        "P0-HD3-DELAY": metric_from_series(delay, min_n=50),
        "P0-HD4-BOUNCE": metric_from_series(bounce, min_n=50),
        "P0-HD4-BREAK": metric_from_series(brk, min_n=50),
        "P0-HD5-FADE": metric_from_series(fade, min_n=30),
        "P0-HD5-CONT": metric_from_series(pin_fwd, min_n=30),
    }


def batch_verdict(results: dict[str, dict]) -> str:
    pull_m = results.get("P0-HD-PULL", {}).get("mean_edge") or 0
    raw_m = results.get("P0-HD-RAW", {}).get("mean_edge") or 0
    if pull_m > raw_m:
        return "conditional"
    if results.get("P0-HD-ALIGN", {}).get("mean_edge", 0) > raw_m:
        return "conditional"
    return "reject"
