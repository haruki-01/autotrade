"""B07 Phase0: rare events."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    merge_htf,
    metric_from_series,
    resample_ohlc,
    spike_revert_edge,
)


def double_spike_indices(df: pd.DataFrame) -> pd.Index:
    spikes = df.loc[df["is_spike"], ["open_time", "spike_dir"]].copy()
    second = []
    for i, (idx, row) in enumerate(spikes.iterrows()):
        t0 = row["open_time"]
        for j in range(i + 1, len(spikes)):
            t1 = spikes.iloc[j]["open_time"]
            if (t1 - t0).total_seconds() > 6 * 3600:
                break
            if spikes.iloc[j]["spike_dir"] != row["spike_dir"]:
                second.append(spikes.index[j])
                break
    return pd.Index(second)


def failed_edge_reversal(df: pd.DataFrame) -> pd.Index:
    idx = []
    for i in range(24, len(df) - 12):
        rh = df["high"].iloc[i - 24 : i].max()
        rl = df["low"].iloc[i - 24 : i].min()
        atr = df["atr14"].iloc[i]
        if np.isnan(atr):
            continue
        touch_high = abs(df["high"].iloc[i] - rh) <= atr * 0.1
        touch_low = abs(df["low"].iloc[i] - rl) <= atr * 0.1
        if touch_high and df["close"].iloc[i + 3] > rh + 0.5 * atr:
            idx.append(df.index[i])
        elif touch_low and df["close"].iloc[i + 3] < rl - 0.5 * atr:
            idx.append(df.index[i])
    return pd.Index(idx)


def week_open_events(df: pd.DataFrame) -> pd.DataFrame:
    """One event per calendar week: first Monday bar after prior Friday close."""
    rows = []
    times = df["open_time"].reset_index(drop=True)
    seen_weeks: set[tuple[int, int]] = set()
    for i in range(1, len(df)):
        if times.iloc[i].weekday() != 0:
            continue
        iso = times.iloc[i].isocalendar()
        week_key = (iso.year, iso.week)
        if week_key in seen_weeks:
            continue
        j = i - 1
        while j >= 0 and times.iloc[j].weekday() != 4:
            j -= 1
        if j < 0:
            continue
        if (times.iloc[i].date() - times.iloc[j].date()).days > 4:
            continue
        gap = (df["open"].iloc[i] - df["close"].iloc[j]) / df["close"].iloc[j]
        if gap == 0:
            continue
        seen_weeks.add(week_key)
        rows.append(
            {
                "idx": df.index[i],
                "bar_i": i,
                "gap": gap,
                "gap_abs": abs(gap),
                "gap_dir": 1 if gap > 0 else -1,
            }
        )
    return pd.DataFrame(rows)


def pre_12h_close_indices(df: pd.DataFrame) -> tuple[pd.Index, pd.Index]:
    h12 = resample_ohlc(df, "12h")
    early = []
    late = []
    for i in range(1, len(h12)):
        close_t = h12["open_time"].iloc[i]
        window_start = close_t - pd.Timedelta(hours=1)
        match = df.loc[(df["open_time"] >= window_start) & (df["open_time"] < close_t)]
        late_match = df.loc[(df["open_time"] >= close_t) & (df["open_time"] < close_t + pd.Timedelta(hours=1))]
        if not match.empty:
            early.append(match.index[-1])
        if not late_match.empty:
            late.append(late_match.index[0])
    return pd.Index(early), pd.Index(late)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    df = merge_htf(df)

    dbl = double_spike_indices(df)
    rev2 = spike_revert_edge(df, "h60", mask=df.index.isin(dbl))

    ha4 = failed_edge_reversal(df)
    ha4_fwd = []
    for idx in ha4:
        i = df.index.get_loc(idx)
        fwd = df["fwd_ret_48"].iloc[i]
        if df["close"].iloc[i] > df["high"].iloc[i - 24 : i].max():
            ha4_fwd.append(fwd)
        else:
            ha4_fwd.append(-fwd)
    ha4_edge = pd.Series(ha4_fwd)
    ha4_false = (ha4_edge < 0).mean() if len(ha4_edge) else np.nan

    gaps = week_open_events(df)
    gap_cont = []
    gap_rev = []
    for _, row in gaps.iterrows():
        idx = row["idx"]
        i = df.index.get_loc(idx)
        fwd = df["fwd_ret_48"].iloc[i]
        if not np.isnan(fwd):
            gap_cont.append(row["gap_dir"] * fwd)
            gap_rev.append(-row["gap_dir"] * fwd)

    early, late = pre_12h_close_indices(df)
    post = []
    for idx in early:
        i = df.index.get_loc(idx)
        regime = df["h1_regime"].iloc[i]
        fwd = df["fwd_ret_48"].iloc[i]
        if not np.isnan(fwd) and regime != 0:
            post.append(regime * fwd)
    ctrl = []
    for idx in late:
        i = df.index.get_loc(idx)
        regime = df["h1_regime"].iloc[i]
        fwd = df["fwd_ret_48"].iloc[i]
        if not np.isnan(fwd) and regime != 0:
            ctrl.append(regime * fwd)

    return {
        "P0-HA3-REVERT2": metric_from_series(rev2, min_n=30, notes=f"double_spike_n={len(dbl)}"),
        "P0-HA3-RATE": {
            "n": len(dbl),
            "mean_edge": len(dbl) / 30,
            "hit_rate": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "insufficient_n" if len(dbl) < 30 else "weak",
            "notes": "",
        },
        "P0-HA4-CONT": metric_from_series(ha4_edge, min_n=50, notes=f"n={len(ha4)}"),
        "P0-HA4-FALSE": {
            "n": len(ha4_edge),
            "hit_rate": ha4_false,
            "mean_edge": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "pass" if ha4_false and ha4_false < 0.5 else "weak",
            "notes": "",
        },
        "P0-HC2-GAP": {
            "n": len(gaps),
            "mean_edge": gaps["gap"].mean() if len(gaps) else np.nan,
            "hit_rate": np.nan,
            "median_edge": gaps["gap"].median() if len(gaps) else np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": gaps["gap"].abs().mean() if len(gaps) else np.nan,
            "vs_baseline": np.nan,
            "verdict": "weak",
            "notes": "",
        },
        "P0-HC2-CONT": metric_from_series(pd.Series(gap_cont), min_n=30),
        "P0-HC2-REVERT": metric_from_series(pd.Series(gap_rev), min_n=30),
        "P0-HB4-POST": metric_from_series(pd.Series(post), min_n=50, notes=f"early_n={len(post)}"),
        "P0-HB4-CTRL": metric_from_series(pd.Series(ctrl), min_n=50, notes=f"late_n={len(ctrl)}"),
    }


def batch_verdict(results: dict[str, dict]) -> str:
    passes = sum(1 for r in results.values() if r.get("verdict") == "pass")
    if passes >= 1:
        return "conditional"
    weaks = sum(1 for r in results.values() if r.get("verdict") == "weak")
    if weaks >= 2:
        return "conditional"
    return "reject"
