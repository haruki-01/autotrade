"""B02 Phase0: SPIKE revert vs continuation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    metric_from_series,
    spike_cont_edge,
    spike_revert_edge,
)

H60 = 12


def compute_path_probs(df: pd.DataFrame) -> dict:
    spikes = df.loc[df["is_spike"]]
    revert_first = cont_first = neither = 0
    for idx in spikes.index:
        i = df.index.get_loc(idx)
        if i + H60 >= len(df):
            continue
        atr = df["atr14"].iloc[i]
        if np.isnan(atr) or atr == 0:
            continue
        direction = int(df["spike_dir"].iloc[i])
        entry = df["close"].iloc[i]
        window = df.iloc[i + 1 : i + 1 + H60]
        rev_hit = cont_hit = False
        for _, row in window.iterrows():
            if direction == 1:
                if row["low"] <= entry - 0.3 * atr:
                    rev_hit = True
                    break
                if row["high"] >= entry + 1.0 * atr:
                    cont_hit = True
                    break
            else:
                if row["high"] >= entry + 0.3 * atr:
                    rev_hit = True
                    break
                if row["low"] <= entry - 1.0 * atr:
                    cont_hit = True
                    break
        if rev_hit:
            revert_first += 1
        elif cont_hit:
            cont_first += 1
        else:
            neither += 1
    n = revert_first + cont_first + neither
    return {
        "n": n,
        "hit_rate": revert_first / n if n else np.nan,
        "mean_edge": (revert_first - cont_first) / n if n else np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": np.nan,
        "verdict": "pass" if n >= 100 and revert_first > cont_first else ("insufficient_n" if n < 100 else "fail"),
        "notes": f"revert_first={revert_first} cont_first={cont_first} neither={neither}",
    }


def compute(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    wd_mask = ~df["is_weekend"]

    revert = spike_revert_edge(df, "h60")
    cont = spike_cont_edge(df, "h60")
    revert15 = spike_revert_edge(df, "h15")
    vs = float(revert.mean() - cont.mean()) if len(revert) and len(cont) else np.nan

    results = {
        "P0-HA-REVERT": metric_from_series(revert, vs_baseline=vs, min_n=100, notes=f"vs CONT diff={vs:.6f}"),
        "P0-HA-CONT": metric_from_series(cont, vs_baseline=-vs if not np.isnan(vs) else None, min_n=100),
        "P0-HA-REVERT15": metric_from_series(revert15, min_n=100, notes="h15 revert after SPIKE"),
        "P0-HA-PATH": compute_path_probs(df),
    }

    sess_notes = []
    for sess in ["TOKYO", "EUROPE_US", "OFF"]:
        rev_s = spike_revert_edge(df, "h60", mask=df["session"] == sess)
        sess_notes.append(f"{sess}:n={len(rev_s)},mean={rev_s.mean():.6f}" if len(rev_s) else f"{sess}:na")
    rev_wd = spike_revert_edge(df, "h60", mask=wd_mask)
    results["P0-HA-BY-SESS"] = metric_from_series(rev_wd, min_n=50, notes="WD-only | " + " | ".join(sess_notes))

    if vs and abs(vs) > 0.00005:
        if vs > 0 and results["P0-HA-REVERT"]["verdict"] == "weak":
            results["P0-HA-REVERT"]["verdict"] = "pass"
        if vs < 0 and results["P0-HA-CONT"]["verdict"] == "weak":
            results["P0-HA-CONT"]["verdict"] = "pass"

    return results


def batch_verdict(results: dict[str, dict]) -> str:
    rev_m = results.get("P0-HA-REVERT", {}).get("mean_edge") or 0
    cont_m = results.get("P0-HA-CONT", {}).get("mean_edge") or 0
    rev_n = results.get("P0-HA-REVERT", {}).get("n", 0)
    if rev_n >= 100 and rev_m > cont_m and rev_m > 0:
        return "promote"
    if rev_n >= 100 and cont_m > rev_m and cont_m > 0:
        return "promote"
    if results.get("P0-HA-REVERT", {}).get("verdict") in ("pass", "weak"):
        return "conditional"
    return "reject"
