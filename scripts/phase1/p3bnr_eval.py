"""P3-B-NR evaluation: H-F3 N-band expansion with detection tuning."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import (
    GATE2_P_TARGET,
    N_BAND_HIGH,
    N_BAND_LOW,
    filter_df_by_split,
)
from scripts.phase1.metrics import fee_breakeven_win_rate, summarize_trades
from scripts.phase1.signals.h_f3_range import generate_hf3_revert_signals

OOS_SPLITS = ("OOS1", "OOS2")
N_TARGET_DEFAULT = 50


@dataclass
class HF3NRConfig:
    cooldown: int = 12
    range_quantile: float = 0.20
    atr_touch_mult: float = 0.10
    roll_bars: int = 24
    rr_ratio: float = 2.0
    pct_risk: float = 0.010
    atr_mult: float = 0.5
    max_bars: int = 24
    n_target: int = N_TARGET_DEFAULT

    def label(self) -> str:
        return (
            f"cd{self.cooldown}_q{int(self.range_quantile * 100)}"
            f"_at{int(self.atr_touch_mult * 100)}_RR{self.rr_ratio:.0f}_R{self.pct_risk}"
        )


def _signal_kwargs(cfg: HF3NRConfig) -> dict:
    return {
        "weekend_filter": True,
        "mode": "revert",
        "cooldown": cfg.cooldown,
        "pct_risk": cfg.pct_risk,
        "atr_mult": cfg.atr_mult,
        "max_bars": cfg.max_bars,
        "rr_ratio": cfg.rr_ratio,
        "range_quantile": cfg.range_quantile,
        "atr_touch_mult": cfg.atr_touch_mult,
        "roll_bars": cfg.roll_bars,
    }


def monthly_n_for_config(df, cfg: HF3NRConfig) -> float:
    all_df = filter_df_by_split(df, "ALL")
    sigs = generate_hf3_revert_signals(all_df, **_signal_kwargs(cfg))
    trades = run_backtest(all_df, sigs, apply_execution=True)
    stats = summarize_trades(trades, all_df, "executed_pnl")
    return stats.get("monthly_n") or 0.0


def find_cooldown_for_n(
    df,
    cfg: HF3NRConfig,
    target_n: int = N_TARGET_DEFAULT,
) -> tuple[int, float]:
    best_cd, best_dist, best_mn = cfg.cooldown, float("inf"), 0.0
    for cd in range(4, 97, 4):
        trial = HF3NRConfig(**{**asdict(cfg), "cooldown": cd})
        mn = monthly_n_for_config(df, trial)
        dist = abs(mn - target_n)
        if dist < best_dist:
            best_dist, best_cd, best_mn = dist, cd, mn
    return best_cd, best_mn


def evaluate_config(df, cfg: HF3NRConfig, *, auto_cooldown: bool = False) -> dict:
    if auto_cooldown:
        cd, tuned_n = find_cooldown_for_n(df, cfg, cfg.n_target)
        cfg = HF3NRConfig(**{**asdict(cfg), "cooldown": cd})
    else:
        tuned_n = monthly_n_for_config(df, cfg)

    sig_kw = _signal_kwargs(cfg)
    split_th, split_ex = {}, {}
    for split in OOS_SPLITS:
        sub = filter_df_by_split(df, split)
        sigs = generate_hf3_revert_signals(sub, **sig_kw)
        th_trades = run_backtest(sub, sigs, apply_execution=False)
        ex_trades = run_backtest(sub, sigs, apply_execution=True)
        split_th[split] = summarize_trades(th_trades, sub, "theoretical_pnl")
        split_ex[split] = summarize_trades(ex_trades, sub, "executed_pnl")

    def _avg(src: dict, attr: str) -> float:
        vals = [src[s].get(attr) for s in OOS_SPLITS if src[s].get(attr) is not None]
        return float(np.mean(vals)) if vals else float("nan")

    th_ev = _avg(split_th, "ev")
    ex_ev = _avg(split_ex, "ev")
    ex_w = _avg(split_ex, "w")
    ex_n = _avg(split_ex, "monthly_n")
    ex_p = _avg(split_ex, "p")
    th_p = _avg(split_th, "p")
    degradation = ex_ev / th_ev if th_ev and not np.isnan(th_ev) and th_ev != 0 else float("nan")

    gate1 = ex_ev > 0 and N_BAND_LOW <= ex_n <= N_BAND_HIGH
    gate2 = ex_p >= GATE2_P_TARGET
    fee_be = fee_breakeven_win_rate(cfg.pct_risk, cfg.pct_risk * cfg.rr_ratio)
    w_check = ex_w >= fee_be if not np.isnan(ex_w) else False

    return {
        "config": asdict(cfg),
        "label": cfg.label(),
        "all_monthly_n_tuned": tuned_n,
        "oos_theoretical_ev": th_ev,
        "oos_theoretical_p": th_p,
        "oos_executed_ev": ex_ev,
        "oos_executed_w": ex_w,
        "oos_executed_n": ex_n,
        "oos_executed_p": ex_p,
        "degradation": degradation,
        "fee_breakeven_w": fee_be,
        "gate1": gate1,
        "gate2": gate2,
        "w_check": w_check,
        "verdict": "pass" if gate2 else ("conditional" if gate1 else "fail"),
        "splits": {"theoretical": split_th, "executed": split_ex},
    }


def pick_best(results: list[dict], key: str = "oos_executed_p") -> dict | None:
    valid = [r for r in results if r.get(key) is not None and not np.isnan(r.get(key))]
    return max(valid, key=lambda r: r[key]) if valid else None


def pick_best_gate1(results: list[dict]) -> dict | None:
    g1 = [r for r in results if r.get("gate1")]
    if g1:
        return max(g1, key=lambda r: r.get("oos_executed_p") or -1e9)
    return pick_best(results)
