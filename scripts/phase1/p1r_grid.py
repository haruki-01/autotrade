"""P1-R: H-D + H-M4 risk-width grid search for Gate2 reachability."""

from __future__ import annotations

from itertools import product

import numpy as np
import pandas as pd

from scripts.phase0.b06_metrics import rsi_exit_os
from scripts.phase0.common import add_features
from scripts.phase1.fast_backtest import fast_run_theoretical
from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import RR_RATIO, Signal, filter_df_by_split
from scripts.phase1.metrics import evaluate_gates, fee_breakeven_win_rate, summarize_trades

BASELINE = {"pct_risk": 0.008, "atr_mult": 0.5, "max_bars": 48, "cooldown": 48}

PCT_RISK_GRID = [0.008, 0.012, 0.016, 0.020, 0.025, 0.030]
ATR_MULT_GRID = [0.5, 1.0, 1.5]
MAX_BARS_GRID = [48, 96]
COOLDOWN_GRID = [48, 96]

SPLITS = ("IS", "OOS1", "OOS2")
OOS_SPLITS = ("OOS1", "OOS2")
TOP_K_VALIDATE = 15


def _risk_width(entry: float, atr: float, pct_risk: float, atr_mult: float) -> float:
    return max(entry * pct_risk, atr_mult * atr)


def _raw_pull_candidates(df: pd.DataFrame) -> list[tuple[int, float, float]]:
    rsi_idx = rsi_exit_os(df)
    raw: list[tuple[int, float, float]] = []
    for idx in rsi_idx:
        i = df.index.get_loc(idx)
        if df["is_weekend"].iloc[i]:
            continue
        if i + 12 >= len(df):
            continue
        window = df.iloc[i + 1 : i + 13]
        if window.empty:
            continue
        entry_i = df.index.get_loc(window["low"].idxmin())
        entry = float(df["close"].iloc[entry_i])
        atr = df["atr14"].iloc[entry_i]
        if np.isnan(atr) or atr <= 0:
            continue
        raw.append((entry_i, entry, float(atr)))
    return raw


def _entry_points(raw: list[tuple[int, float, float]], cooldown: int) -> list[tuple[int, float, float]]:
    points: list[tuple[int, float, float]] = []
    last_bar = -cooldown
    for entry_i, entry, atr in raw:
        if entry_i <= last_bar + cooldown:
            continue
        points.append((entry_i, entry, atr))
        last_bar = entry_i
    return points


def _signals_from_points(
    points: list[tuple[int, float, float]],
    pct_risk: float,
    atr_mult: float,
    max_bars: int,
) -> list[Signal]:
    return [
        Signal(
            bar_idx=entry_i,
            direction=1,
            entry_price=entry,
            sl_price=entry - _risk_width(entry, atr, pct_risk, atr_mult),
            tp_price=entry + RR_RATIO * _risk_width(entry, atr, pct_risk, atr_mult),
            max_bars=max_bars,
            tag="hd_pull",
        )
        for entry_i, entry, atr in points
    ]


def _prepare_splits(df) -> dict[str, tuple[pd.DataFrame, dict[int, list]]]:
    cache: dict[str, tuple[pd.DataFrame, dict[int, list]]] = {}
    for split in SPLITS:
        sub = filter_df_by_split(df, split)
        featured = add_features(sub)
        raw = _raw_pull_candidates(featured)
        by_cd = {cd: _entry_points(raw, cd) for cd in COOLDOWN_GRID}
        cache[split] = (featured, by_cd)
    return cache


def _eval_params(cache, params: dict, executed: bool) -> dict[str, dict]:
    pnl_attr = "executed_pnl" if executed else "theoretical_pnl"
    out: dict[str, dict] = {}
    for split in SPLITS:
        sub, by_cd = cache[split]
        sigs = _signals_from_points(by_cd[params["cooldown"]], params["pct_risk"], params["atr_mult"], params["max_bars"])
        if executed:
            trades = run_backtest(sub, sigs, apply_execution=True)
            stats = summarize_trades(trades, sub, pnl_attr)
        else:
            fast = fast_run_theoretical(sub, sigs)
            pnls = [p for p, _ in fast]
            months = max((sub["open_time"].max() - sub["open_time"].min()).days / 30.44, 1)
            n = len(pnls)
            stats = {
                "n": n,
                "w": sum(1 for p in pnls if p > 0) / n if n else np.nan,
                "ev": float(np.mean(pnls)) if n else np.nan,
                "monthly_n": n / months if n else np.nan,
                "p": (float(np.mean(pnls)) * n / months) if n else np.nan,
                "max_dd": np.nan,
            }
        gate1, gate2 = evaluate_gates(stats)
        sl_pct = params["pct_risk"]
        out[split] = {
            **stats,
            "gate1": gate1,
            "gate2": gate2,
            "fee_breakeven_w": fee_breakeven_win_rate(sl_pct, sl_pct * 2),
        }
    oos_ps = [out[s]["p"] for s in OOS_SPLITS if out[s].get("p") is not None and not np.isnan(out[s]["p"])]
    out["_summary"] = {
        "oos_avg_p": float(np.mean(oos_ps)) if oos_ps else np.nan,
        "gate1_both_oos": all(out[s].get("gate1") for s in OOS_SPLITS),
        "gate2_any_oos": any(out[s].get("gate2") for s in OOS_SPLITS),
        "gate2_both_oos": all(out[s].get("gate2") for s in OOS_SPLITS),
    }
    return out


def _score_row(summary: dict) -> float:
    score = summary["oos_avg_p"] if not np.isnan(summary["oos_avg_p"]) else -1e9
    if summary["gate2_both_oos"]:
        return score + 1e6
    if summary["gate2_any_oos"]:
        return score + 1e5
    if summary["gate1_both_oos"]:
        return score + 1e4
    return score


def compute(df) -> dict:
    cache = _prepare_splits(df)
    print("  Phase1: theoretical grid scan...", flush=True)
    theoretical_rows: list[dict] = []

    for pct_risk, atr_mult, max_bars, cooldown in product(
        PCT_RISK_GRID, ATR_MULT_GRID, MAX_BARS_GRID, COOLDOWN_GRID
    ):
        params = {"pct_risk": pct_risk, "atr_mult": atr_mult, "max_bars": max_bars, "cooldown": cooldown}
        evaled = _eval_params(cache, params, executed=False)
        summary = evaled["_summary"]
        theoretical_rows.append({"params": params, **{s: evaled[s] for s in SPLITS}, **summary})

    theoretical_rows.sort(key=lambda r: _score_row(r), reverse=True)
    top_params = {tuple(sorted(r["params"].items())) for r in theoretical_rows[:TOP_K_VALIDATE]}

    print("  Phase1: executed validation on top combos...", flush=True)
    validated: list[dict] = []
    for row in theoretical_rows:
        key = tuple(sorted(row["params"].items()))
        if key not in top_params and not row.get("gate2_any_oos"):
            continue
        ex = _eval_params(cache, row["params"], executed=True)
        validated.append(
            {
                "params": row["params"],
                "theoretical": {s: row[s] for s in SPLITS},
                "executed": {s: ex[s] for s in SPLITS},
                **ex["_summary"],
            }
        )

    validated.sort(key=lambda r: _score_row(r), reverse=True)
    baseline_ex = _eval_params(cache, BASELINE, executed=True)
    best = validated[0] if validated else None

    gate2_hits = [r for r in validated if r.get("gate2_any_oos")]
    gate1_hits = [r for r in validated if r.get("gate1_both_oos")]

    def _pack_best(row: dict | None, prefix: str) -> dict:
        if not row:
            return {}
        out = {"params": row["params"]}
        for s in SPLITS:
            out[s] = row["executed"][s]
        out["oos_avg_p"] = row.get("oos_avg_p")
        out["gate1_both_oos"] = row.get("gate1_both_oos")
        out["gate2_any_oos"] = row.get("gate2_any_oos")
        out["gate2_both_oos"] = row.get("gate2_both_oos")
        out["notes"] = prefix
        return out

    metrics = {
        "P1R-BASELINE": {
            "params": BASELINE,
            **{s: baseline_ex[s] for s in SPLITS},
            **baseline_ex["_summary"],
            "notes": "P1-A default R width (executed)",
        },
        "P1R-BEST": _pack_best(best, "top validated executed"),
        "P1R-GRID-STATS": {
            "n_combos": len(theoretical_rows),
            "n_validated_executed": len(validated),
            "gate2_any_count": len(gate2_hits),
            "gate1_both_count": len(gate1_hits),
            "notes": f"screen=theoretical validate_top={TOP_K_VALIDATE}",
        },
    }

    return {
        "metrics": metrics,
        "grid": validated,
        "gate2_combos": gate2_hits[:10],
        "gate1_combos": gate1_hits[:10],
        "theoretical_top10": theoretical_rows[:10],
    }


def batch_verdict(results: dict) -> str:
    best = results.get("metrics", {}).get("P1R-BEST", {})
    if best.get("gate2_both_oos"):
        return "promote"
    if best.get("gate2_any_oos"):
        return "conditional"
    if best.get("gate1_both_oos"):
        return "conditional"
    return "reject"
