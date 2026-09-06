"""B10: MFE/MAE excursion analysis for exit design."""

from __future__ import annotations

import numpy as np

from datetime import date

from scripts.phase0.common import load_or_fetch
from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.p3bnr_eval import HF3NRConfig, _signal_kwargs
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals
from scripts.phase1.signals.h_f3_range import generate_hf3_revert_signals
from scripts.phase1.validation.risk_metrics import summarize_excursions


def _excursion_stats(trades, split: str, strategy: str) -> dict:
    filled = [t for t in trades if t.filled]
    exc = summarize_excursions(trades)
    pnls = [t.executed_pnl for t in filled]
    wins = [t for t in filled if t.executed_pnl > 0]
    losses = [t for t in filled if t.executed_pnl <= 0]
    return {
        "split": split,
        "strategy": strategy,
        "n": len(filled),
        "w": len(wins) / len(filled) if filled else float("nan"),
        **exc,
        "median_mfe_pct": float(np.median([t.mfe_pct for t in filled])) if filled else float("nan"),
        "median_mae_pct": float(np.median([t.mae_pct for t in filled])) if filled else float("nan"),
        "pct_mfe_gt_1pct": float(np.mean([t.mfe_pct >= 0.01 for t in filled])) if filled else float("nan"),
        "pct_mae_gt_1pct": float(np.mean([t.mae_pct >= 0.01 for t in filled])) if filled else float("nan"),
        "avg_win_mfe": float(np.mean([t.mfe_pct for t in wins])) if wins else float("nan"),
        "avg_loss_mae": float(np.mean([t.mae_pct for t in losses])) if losses else float("nan"),
    }


def _tp_sl_grid_analysis(trades, tp_candidates: list[float], sl_candidates: list[float]) -> list[dict]:
    """Theoretical hit rates if TP/SL were placed at fixed pct levels."""
    filled = [t for t in trades if t.filled]
    if not filled:
        return []
    rows = []
    for tp in tp_candidates:
        for sl in sl_candidates:
            tp_hits = sum(1 for t in filled if t.mfe_pct >= tp)
            sl_hits = sum(1 for t in filled if t.mae_pct >= sl)
            rows.append(
                {
                    "tp_pct": tp,
                    "sl_pct": sl,
                    "tp_hit_rate": tp_hits / len(filled),
                    "sl_hit_rate": sl_hits / len(filled),
                    "tp_before_sl_proxy": tp_hits / max(sl_hits, 1),
                }
            )
    return rows


def compute_hd(df) -> dict:
    metrics = {}
    for split in ("TRAIN", "VALIDATION"):
        sub = filter_df_by_split(df, split)
        sigs = generate_hd_pull_signals(sub, weekend_filter=True, mode="pull")
        trades = run_backtest(sub, sigs, apply_execution=True)
        key = f"B10-HD-MFE_{split}"
        metrics[key] = _excursion_stats(trades, split, "H-D")
        metrics[f"{key}-GRID"] = _tp_sl_grid_analysis(
            trades,
            tp_candidates=[0.005, 0.010, 0.015, 0.020],
            sl_candidates=[0.005, 0.008, 0.010, 0.015],
        )
    return metrics


def compute_hf3(df, cfg: HF3NRConfig | None = None) -> dict:
    cfg = cfg or HF3NRConfig(cooldown=4, range_quantile=0.40, atr_touch_mult=0.20)
    sig_kw = _signal_kwargs(cfg)
    metrics = {}
    for split in ("TRAIN", "VALIDATION"):
        sub = filter_df_by_split(df, split)
        sigs = generate_hf3_revert_signals(sub, **sig_kw)
        trades = run_backtest(sub, sigs, apply_execution=True)
        key = f"B10-HF3-MFE_{split}"
        metrics[key] = _excursion_stats(trades, split, "H-F3")
        metrics[key]["config"] = cfg.label()
        metrics[f"{key}-GRID"] = _tp_sl_grid_analysis(
            trades,
            tp_candidates=[0.005, 0.010, 0.015, 0.020],
            sl_candidates=[0.005, 0.010, 0.015],
        )
    return metrics


def compute(df, strategy: str = "all", hf3_config: HF3NRConfig | None = None) -> dict:
    if strategy == "hd":
        return compute_hd(df)
    if strategy == "hf3":
        return compute_hf3(df, hf3_config)
    return {**compute_hd(df), **compute_hf3(df, hf3_config)}


def batch_verdict(results: dict) -> str:
    hd_val = results.get("B10-HD-MFE_VALIDATION", {})
    hf3_val = results.get("B10-HF3-MFE_VALIDATION", {})
    if hd_val.get("mfe_mae_ratio", 0) > 1.0 or hf3_val.get("mfe_mae_ratio", 0) > 1.0:
        return "conditional"
    return "reject"


def main(strategy: str = "all") -> dict:
    df = load_or_fetch(date(2024, 1, 1), date(2026, 8, 31))
    results = compute(df, strategy=strategy)
    out = {
        "batch_id": "B10",
        "strategy_filter": strategy,
        "results": results,
        "batch_verdict": batch_verdict(results),
    }
    return out
