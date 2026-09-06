"""B11 Phase0: H-F4 thrust decay — revert vs continuation edge."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, metric_from_series, months_in_sample

H240 = 48  # 48 bars = h240 on 5m


def detect_thrust_decay(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """THRUST_DECAY: momentum run then decreasing body size."""
    out = pd.Series(False, index=df.index)
    thrust_dir = pd.Series(0, index=df.index, dtype=int)

    body = df["body"]
    body_med = df["body_med100"]
    close = df["close"]

    for i in range(6, len(df) - H240 - 1):
        if np.isnan(body_med.iloc[i]) or body_med.iloc[i] <= 0:
            continue
        # Prior thrust: 3 consecutive same-direction bars with large bodies
        dirs = []
        for j in range(i - 3, i):
            d = 1 if close.iloc[j] > close.iloc[j - 1] else (-1 if close.iloc[j] < close.iloc[j - 1] else 0)
            if d == 0 or body.iloc[j] < body_med.iloc[j] * 1.0:
                dirs = []
                break
            dirs.append(d)
        if len(dirs) != 3 or not (dirs[0] == dirs[1] == dirs[2]):
            continue
        # Decay: last 2 bars before i have shrinking bodies
        if not (body.iloc[i - 1] < body.iloc[i - 2] < body.iloc[i - 3]):
            continue
        out.iloc[i] = True
        thrust_dir.iloc[i] = dirs[-1]
    return out, thrust_dir


def _forward_edges(df: pd.DataFrame, mask: pd.Series, thrust_dir: pd.Series, mode: str) -> pd.Series:
    edges = []
    idx_list = df.index[mask]
    for idx in idx_list:
        i = df.index.get_loc(idx)
        if i + H240 >= len(df):
            continue
        td = int(thrust_dir.loc[idx])
        if td == 0:
            continue
        entry = df["close"].iloc[i]
        exit_p = df["close"].iloc[i + H240]
        ret = exit_p / entry - 1
        if mode == "revert":
            edges.append(-td * ret)
        else:
            edges.append(td * ret)
    return pd.Series(edges)


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    is_decay, thrust_dir = detect_thrust_decay(df)
    df = df.copy()
    df["is_thrust_decay"] = is_decay
    df["thrust_dir"] = thrust_dir

    n_events = int(is_decay.sum())
    rev = _forward_edges(df, is_decay, thrust_dir, "revert")
    cont = _forward_edges(df, is_decay, thrust_dir, "cont")
    vs = float(rev.mean() - cont.mean()) if len(rev) and len(cont) else np.nan

    results = {
        "P0-HF4-REV": metric_from_series(
            rev, vs_baseline=vs, min_n=30, notes=f"THRUST_DECAY revert h240, events={n_events}"
        ),
        "P0-HF4-CONT": metric_from_series(
            cont, vs_baseline=-vs if not np.isnan(vs) else None, min_n=30, notes="THRUST_DECAY continuation h240"
        ),
        "P0-HF4-FREQ": {
            "n": n_events,
            "events_per_month": n_events / months_in_sample(df),
            "verdict": "pass" if n_events >= 100 else ("insufficient_n" if n_events < 30 else "conditional"),
        },
    }
    return results


def batch_verdict(results: dict[str, dict]) -> str:
    rev = results.get("P0-HF4-REV", {})
    cont = results.get("P0-HF4-CONT", {})
    if rev.get("verdict") == "pass" and (rev.get("mean_edge") or 0) > (cont.get("mean_edge") or 0):
        return "promote"
    if rev.get("verdict") in ("pass", "weak") or cont.get("verdict") in ("pass", "weak"):
        return "conditional"
    if results.get("P0-HF4-FREQ", {}).get("verdict") == "insufficient_n":
        return "defer"
    return "reject"
