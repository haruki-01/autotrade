"""B01 Phase0 metrics: H-E, H-C, H-C4 session/time structure."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.phase0.common import (
    add_features,
    load_or_fetch,
    summarize_returns,
    verdict_from_stats,
    window_mask,
)

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)


def daily_window_returns(df: pd.DataFrame, sh: int, sm: int, eh: int, em: int) -> pd.Series:
    mask = window_mask(df, sh, sm, eh, em)
    sub = df.loc[mask].copy()
    sub["date"] = sub["open_time"].dt.date
    grouped = sub.groupby("date")
    rets = grouped.apply(lambda g: g["close"].iloc[-1] / g["open"].iloc[0] - 1 if len(g) >= 2 else np.nan)
    return rets.dropna()


def random_baseline_windows(df: pd.DataFrame, n_samples: int, window_bars: int = 12, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    max_i = len(df) - window_bars - 1
    if max_i <= 0:
        return pd.Series(dtype=float)
    idx = rng.integers(0, max_i, size=n_samples)
    rets = []
    for i in idx:
        o = df["open"].iloc[i]
        c = df["close"].iloc[i + window_bars - 1]
        rets.append(c / o - 1)
    return pd.Series(rets)


def run_length_same_sign(returns: pd.Series) -> float:
    if returns.empty:
        return np.nan
    signs = np.sign(returns.dropna())
    if len(signs) == 0:
        return np.nan
    runs = []
    cur = 1
    for i in range(1, len(signs)):
        if signs.iloc[i] == signs.iloc[i - 1] and signs.iloc[i] != 0:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return float(np.mean(runs))


def spike_revert_edge(df: pd.DataFrame, session: str | None = None) -> pd.Series:
    sub = df.loc[df["is_spike"]].copy()
    if session:
        sub = sub.loc[sub["session"] == session]
    edge = np.where(sub["spike_dir"] == 1, -sub["fwd_ret_12"], sub["fwd_ret_12"])
    return pd.Series(edge, index=sub.index).dropna()


def compute_b01(df: pd.DataFrame) -> dict[str, dict]:
    df = add_features(df)
    results: dict[str, dict] = {}

    fee_rets = daily_window_returns(df, 5, 30, 6, 30)
    fee_stats = summarize_returns(fee_rets)
    baseline = random_baseline_windows(df, n_samples=max(len(fee_rets) * 3, 500), window_bars=12)
    base_stats = summarize_returns(baseline)
    vs = fee_stats["mean_edge"] - base_stats["mean_edge"] if fee_stats["n"] and base_stats["n"] else np.nan

    fee_mask = window_mask(df, 5, 30, 6, 30)
    other_mask = ~fee_mask
    fee_vol = df.loc[fee_mask, "range"].mean()
    other_vol = df.loc[other_mask, "range"].mean()

    pre_rets = daily_window_returns(df, 5, 0, 5, 30)
    post_rets = daily_window_returns(df, 6, 30, 7, 0)

    results["P0-HE-RET"] = {
        **fee_stats,
        "vs_baseline": vs,
        "verdict": verdict_from_stats(fee_stats, vs, min_n=100),
        "notes": "Daily FEE_WINDOW 05:30-06:30 return (first open -> last close)",
    }
    results["P0-HE-VS"] = {
        "n": int(fee_stats["n"]),
        "mean_edge": float(vs) if not np.isnan(vs) else np.nan,
        "hit_rate": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": 0.0,
        "verdict": "pass" if vs and vs > 0.0001 else ("weak" if vs and vs > 0 else "fail"),
        "notes": f"fee_mean={fee_stats['mean_edge']:.6f} baseline_mean={base_stats['mean_edge']:.6f}",
    }
    results["P0-HE-VOL"] = {
        "n": int(fee_mask.sum()),
        "mean_edge": float(fee_vol / other_vol - 1) if other_vol else np.nan,
        "hit_rate": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": float(fee_vol),
        "vs_baseline": float(fee_vol - other_vol),
        "verdict": "pass" if fee_vol > other_vol * 1.05 else ("weak" if fee_vol > other_vol else "fail"),
        "notes": f"fee_range_mean={fee_vol:.0f} other_range_mean={other_vol:.0f}",
    }
    results["P0-HE-DIR"] = {
        **fee_stats,
        "vs_baseline": vs,
        "verdict": "pass"
        if fee_stats["hit_rate"] and (fee_stats["hit_rate"] >= 0.55 or fee_stats["hit_rate"] <= 0.45)
        else "fail",
        "notes": "Directional bias in FEE_WINDOW daily returns",
    }
    pre_s = summarize_returns(pre_rets)
    post_s = summarize_returns(post_rets)
    results["P0-HE-PREPOST"] = {
        "n": int(pre_s["n"]),
        "mean_edge": float(pre_s["mean_edge"] - post_s["mean_edge"]) if pre_s["n"] and post_s["n"] else np.nan,
        "hit_rate": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": float(pre_s["mean_edge"] - post_s["mean_edge"]) if pre_s["n"] and post_s["n"] else np.nan,
        "verdict": "weak" if pre_s["n"] and post_s["n"] else "insufficient_n",
        "notes": f"pre_mean={pre_s.get('mean_edge')} post_mean={post_s.get('mean_edge')}",
    }

    wd = df.loc[~df["is_weekend"], "fwd_ret_12"].dropna()
    we = df.loc[df["is_weekend"], "fwd_ret_12"].dropna()
    wd_s = summarize_returns(wd)
    we_s = summarize_returns(we)
    results["P0-HC4-WDWE"] = {
        "n": int(wd_s["n"] + we_s["n"]),
        "hit_rate": float(wd_s["hit_rate"] - we_s["hit_rate"]) if wd_s["n"] and we_s["n"] else np.nan,
        "mean_edge": float(wd_s["mean_edge"] - we_s["mean_edge"]) if wd_s["n"] and we_s["n"] else np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": float(df.loc[~df["is_weekend"], "range"].mean() - df.loc[df["is_weekend"], "range"].mean()),
        "vs_baseline": float(wd_s["mean_edge"] - we_s["mean_edge"]) if wd_s["n"] and we_s["n"] else np.nan,
        "verdict": "pass" if we_s["mean_edge"] is not None and wd_s["mean_edge"] and wd_s["mean_edge"] > we_s["mean_edge"] else "weak",
        "notes": f"WD mean_fwd={wd_s.get('mean_edge')} WE mean_fwd={we_s.get('mean_edge')}",
    }

    we_spike = df.loc[df["is_weekend"] & df["is_spike"], "spike_cont_fail"].dropna()
    results["P0-HC4-FAKEBRK"] = {
        "n": int(len(we_spike)),
        "hit_rate": float(we_spike.mean()) if len(we_spike) else np.nan,
        "mean_edge": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": np.nan,
        "verdict": "pass"
        if len(we_spike) >= 30 and we_spike.mean() > 0.55
        else ("insufficient_n" if len(we_spike) < 30 else "fail"),
        "notes": "WE spike continuation fail rate (h60)",
    }

    tokyo = df.loc[df["session"] == "TOKYO", "fwd_ret_12"].dropna()
    eu = df.loc[df["session"] == "EUROPE_US", "fwd_ret_12"].dropna()
    off = df.loc[df["session"] == "OFF", "fwd_ret_12"].dropna()
    parts_ret = [f"TOKYO:{tokyo.mean():.6f}", f"EUROPE_US:{eu.mean():.6f}", f"OFF:{off.mean():.6f}"]
    vs_sess = float(eu.mean() - tokyo.mean()) if len(eu) and len(tokyo) else np.nan
    results["P0-HC-RET"] = {
        **summarize_returns(pd.concat([tokyo, eu, off])),
        "vs_baseline": vs_sess,
        "verdict": "pass" if vs_sess and abs(vs_sess) > 0.00005 else "weak",
        "notes": " | ".join(parts_ret),
    }

    parts_vol = [
        f"TOKYO:{df.loc[df['session']=='TOKYO','range'].mean():.0f}",
        f"EUROPE_US:{df.loc[df['session']=='EUROPE_US','range'].mean():.0f}",
        f"OFF:{df.loc[df['session']=='OFF','range'].mean():.0f}",
    ]
    results["P0-HC-VOL"] = {
        "n": int(len(df)),
        "mean_edge": float(
            df.loc[df["session"] == "EUROPE_US", "range"].mean() / df.loc[df["session"] == "TOKYO", "range"].mean() - 1
        )
        if len(tokyo)
        else np.nan,
        "hit_rate": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": np.nan,
        "verdict": "weak",
        "notes": " | ".join(parts_vol),
    }

    trend_parts = []
    eu_run = run_length_same_sign(df.loc[df["session"] == "EUROPE_US", "ret"].dropna())
    tokyo_run = run_length_same_sign(df.loc[df["session"] == "TOKYO", "ret"].dropna())
    for sess in ["TOKYO", "EUROPE_US", "OFF"]:
        r = df.loc[df["session"] == sess, "ret"].dropna()
        trend_parts.append(f"{sess}_run={run_length_same_sign(r):.2f}")
    results["P0-HC-TREND"] = {
        "n": int(len(df)),
        "mean_edge": float(eu_run - tokyo_run) if not np.isnan(eu_run) and not np.isnan(tokyo_run) else np.nan,
        "hit_rate": np.nan,
        "median_edge": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "mean_abs_move": np.nan,
        "vs_baseline": float(eu_run - tokyo_run) if not np.isnan(eu_run) and not np.isnan(tokyo_run) else np.nan,
        "verdict": "pass" if eu_run and tokyo_run and eu_run > tokyo_run else "weak",
        "notes": " | ".join(trend_parts),
    }

    rev_parts = []
    tokyo_rev = spike_revert_edge(df, "TOKYO")
    eu_rev = spike_revert_edge(df, "EUROPE_US")
    for sess in ["TOKYO", "EUROPE_US", "OFF"]:
        edge = spike_revert_edge(df, sess)
        rev_parts.append(f"{sess}_revert_mean={edge.mean():.6f}" if len(edge) else f"{sess}_revert_mean=na")
    results["P0-HC-REVERT"] = {
        **summarize_returns(tokyo_rev),
        "vs_baseline": float(tokyo_rev.mean() - eu_rev.mean()) if len(tokyo_rev) and len(eu_rev) else np.nan,
        "verdict": "pass"
        if len(tokyo_rev) >= 30 and tokyo_rev.mean() > 0
        else ("insufficient_n" if len(tokyo_rev) < 30 else "weak"),
        "notes": " | ".join(rev_parts),
    }

    return results


compute = compute_b01


def batch_verdict(results: dict[str, dict]) -> str:
    passes = sum(1 for r in results.values() if r.get("verdict") == "pass")
    weaks = sum(1 for r in results.values() if r.get("verdict") == "weak")
    if passes >= 3:
        return "conditional"
    if passes + weaks >= 4:
        return "conditional"
    if passes >= 1:
        return "conditional"
    return "reject"


def main() -> None:
    df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    print(f"Loaded {len(df)} bars ({df['open_time'].min()} .. {df['open_time'].max()})")
    results = compute_b01(df)
    out_dir = Path(__file__).resolve().parents[2] / "data" / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "b01_results.json"
    payload = {
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "n_bars": len(df),
        "batch_id": "B01",
        "batch_verdict": batch_verdict(results),
        "metrics": results,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
