"""B05 Phase0: TREND_EXCESS_PULL resume vs control."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, merge_htf, metric_from_series, months_in_sample, resample_ohlc


def _attach_h1_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add 1h thrust stats aligned to 5m bars."""
    out = df.copy()
    h1 = resample_ohlc(out, "1h")
    h1["ema20"] = h1["close"].ewm(span=20, adjust=False).mean()
    h1["roll_high20"] = h1["high"].rolling(20, min_periods=20).max()
    h1["roll_low20"] = h1["low"].rolling(20, min_periods=20).min()
    h1["roll_range20"] = h1["roll_high20"] - h1["roll_low20"]
    h1["thrust_up"] = (h1["close"] >= h1["roll_high20"] - 0.05 * h1["roll_range20"]) & (h1["roll_range20"] > 0)
    h1["thrust_down"] = (h1["close"] <= h1["roll_low20"] + 0.05 * h1["roll_range20"]) & (h1["roll_range20"] > 0)
    return pd.merge_asof(
        out.sort_values("open_time"),
        h1[["open_time", "thrust_up", "thrust_down", "roll_range20"]],
        on="open_time",
        direction="backward",
    )


def detect_trend_pull_events(df: pd.DataFrame) -> tuple[pd.Index, pd.Index]:
    """TREND_EXCESS_PULL per phase0-stats §3.19: 12h regime + 1h excess thrust + pullback."""
    resume_idx: list = []
    ctrl_idx: list = []
    last_resume = last_ctrl = -999

    for i in range(240, len(df) - 48):
        regime = int(df["h12_regime"].iloc[i])
        if regime == 0:
            continue

        h12_close = df["h12_close"].iloc[i]
        h12_ema50 = df["h12_ema50"].iloc[i]
        h1_ema = df["h1_ema20"].iloc[i]
        price = df["close"].iloc[i]
        if np.isnan(h12_close) or np.isnan(h12_ema50) or np.isnan(h1_ema):
            continue

        if regime == 1:
            if h12_close <= h12_ema50:
                continue
            if not df["thrust_up"].iloc[i]:
                continue
            recent = df.iloc[i - 48 : i]
            was_extended = (recent["close"] > h1_ema * 1.008).any()
            near_ema = h1_ema * 0.997 <= price <= h1_ema * 1.003
            if was_extended and near_ema and i - last_resume >= 48:
                resume_idx.append(df.index[i])
                last_resume = i
            extended_now = price > h1_ema * 1.008
            rising = df["close"].iloc[i] > df["close"].iloc[i - 12]
            if extended_now and rising and i - last_ctrl >= 48:
                ctrl_idx.append(df.index[i])
                last_ctrl = i
        else:
            if h12_close >= h12_ema50:
                continue
            if not df["thrust_down"].iloc[i]:
                continue
            recent = df.iloc[i - 48 : i]
            was_extended = (recent["close"] < h1_ema * 0.992).any()
            near_ema = h1_ema * 0.997 <= price <= h1_ema * 1.003
            if was_extended and near_ema and i - last_resume >= 48:
                resume_idx.append(df.index[i])
                last_resume = i
            extended_now = price < h1_ema * 0.992
            falling = df["close"].iloc[i] < df["close"].iloc[i - 12]
            if extended_now and falling and i - last_ctrl >= 48:
                ctrl_idx.append(df.index[i])
                last_ctrl = i

    return pd.Index(resume_idx), pd.Index(ctrl_idx)


def regime_edge(df: pd.DataFrame, indices: pd.Index) -> pd.Series:
    edges = []
    for idx in indices:
        i = df.index.get_loc(idx)
        regime = df["h12_regime"].iloc[i]
        fwd = df["fwd_ret_48"].iloc[i]
        if not np.isnan(fwd) and regime != 0:
            edges.append(regime * fwd)
    return pd.Series(edges)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    df = merge_htf(df)
    df = _attach_h1_features(df)
    resume_idx, ctrl_idx = detect_trend_pull_events(df)
    resume = regime_edge(df, resume_idx)
    ctrl = regime_edge(df, ctrl_idx)
    vs = float(resume.mean() - ctrl.mean()) if len(resume) and len(ctrl) else np.nan
    months = months_in_sample(df)

    return {
        "P0-HF1-RESUME": metric_from_series(resume, vs_baseline=vs, min_n=50, notes=f"vs CTRL={vs}"),
        "P0-HF1-CTRL": metric_from_series(ctrl, min_n=50),
        "P0-HF1-FREQ": {
            "n": len(resume_idx),
            "mean_edge": len(resume_idx) / months,
            "hit_rate": np.nan,
            "median_edge": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "mean_abs_move": np.nan,
            "vs_baseline": np.nan,
            "verdict": "weak",
            "notes": f"events/month={len(resume_idx)/months:.1f}",
        },
    }


def batch_verdict(results: dict[str, dict]) -> str:
    r = results.get("P0-HF1-RESUME", {})
    c = results.get("P0-HF1-CTRL", {})
    if r.get("mean_edge", 0) > (c.get("mean_edge") or 0) and r.get("n", 0) >= 50:
        return "conditional" if r.get("mean_edge", 0) > 0 else "reject"
    return "reject"
