"""H-D4 Phase1 evaluation helpers."""

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
from scripts.phase1.signals.h_d4_pct import generate_hd4_signals

OOS_SPLITS = ("OOS1", "OOS2")
ALL_SPLITS = ("IS", "OOS1", "OOS2")


@dataclass
class HD4Config:
    mode: str = "break"
    pct_level: float = -0.015
    swing_bars: int = 24
    entry_mode: str = "immediate"
    cooldown: int | None = 48
    sl_pct: float | None = 0.005
    tp_pct: float | None = 0.010
    pct_risk: float = 0.008
    atr_mult: float = 0.5
    max_bars: int = 48
    rr_ratio: float = 2.0
    n_target: int = 50
    weekend_filter: bool = True

    def label(self) -> str:
        cd = self.cooldown if self.cooldown is not None else "auto"
        pct = f"{abs(self.pct_level) * 100:.1f}%"
        return (
            f"{self.mode}_{pct}_sw{self.swing_bars}_{self.entry_mode}"
            f"_cd{cd}_mb{self.max_bars}"
        )


def _signal_kwargs(cfg: HD4Config, cooldown: int) -> dict:
    use_atr = cfg.sl_pct is None or cfg.tp_pct is None
    return {
        "mode": cfg.mode,
        "pct_level": cfg.pct_level,
        "swing_bars": cfg.swing_bars,
        "entry_mode": cfg.entry_mode,
        "weekend_filter": cfg.weekend_filter,
        "cooldown": cooldown,
        "sl_pct": None if use_atr else cfg.sl_pct,
        "tp_pct": None if use_atr else cfg.tp_pct,
        "pct_risk": cfg.pct_risk,
        "atr_mult": cfg.atr_mult,
        "max_bars": cfg.max_bars,
        "rr_ratio": cfg.rr_ratio,
    }


def resolve_cooldown(df, cfg: HD4Config) -> int:
    if cfg.cooldown is not None:
        return cfg.cooldown
    all_df = filter_df_by_split(df, "ALL")
    lo, hi = 12, 576
    best_cd, best_dist = 48, float("inf")
    # Coarse pass (step 48) then fine (step 12)
    for step in (48, 12):
        for cd in range(lo, hi + 1, step):
            sig_kw = _signal_kwargs(cfg, cd)
            sigs = generate_hd4_signals(all_df, **sig_kw)
            trades = run_backtest(all_df, sigs, apply_execution=True)
            stats = summarize_trades(trades, all_df, "executed_pnl")
            mn = stats.get("monthly_n") or 0.0
            dist = abs(mn - cfg.n_target)
            if dist < best_dist:
                best_dist, best_cd = dist, cd
        lo = max(12, best_cd - 48)
        hi = min(576, best_cd + 48)
    return best_cd


def evaluate_config(df, cfg: HD4Config, cooldown: int | None = None) -> dict:
    cd = cooldown if cooldown is not None else resolve_cooldown(df, cfg)
    cfg_resolved = HD4Config(**{**asdict(cfg), "cooldown": cd})
    sig_kw = _signal_kwargs(cfg_resolved, cd)

    split_th, split_ex = {}, {}
    for split in ALL_SPLITS:
        sub = filter_df_by_split(df, split)
        sigs = generate_hd4_signals(sub, **sig_kw)
        th_trades = run_backtest(sub, sigs, apply_execution=False)
        ex_trades = run_backtest(sub, sigs, apply_execution=True)
        split_th[split] = summarize_trades(th_trades, sub, "theoretical_pnl")
        split_ex[split] = summarize_trades(ex_trades, sub, "executed_pnl")

    def _avg(src: dict, attr: str, splits=OOS_SPLITS) -> float:
        vals = [src[s].get(attr) for s in splits if src[s].get(attr) is not None]
        return float(np.mean(vals)) if vals else float("nan")

    th_ev = _avg(split_th, "ev")
    ex_ev = _avg(split_ex, "ev")
    ex_w = _avg(split_ex, "w")
    ex_n = _avg(split_ex, "monthly_n")
    ex_p = _avg(split_ex, "p")
    th_p = _avg(split_th, "p")
    is_ex_ev = split_ex["IS"].get("ev")
    is_ex_n = split_ex["IS"].get("monthly_n")
    degradation = ex_ev / th_ev if th_ev and not np.isnan(th_ev) and th_ev != 0 else float("nan")

    sl = cfg_resolved.sl_pct or cfg_resolved.pct_risk
    tp = cfg_resolved.tp_pct or cfg_resolved.pct_risk * cfg_resolved.rr_ratio
    fee_be = fee_breakeven_win_rate(sl, tp)

    gate1 = ex_ev > 0 and N_BAND_LOW <= ex_n <= N_BAND_HIGH
    gate2 = ex_p >= GATE2_P_TARGET

    return {
        "config": asdict(cfg_resolved),
        "label": cfg_resolved.label(),
        "oos_theoretical_ev": th_ev,
        "oos_theoretical_p": th_p,
        "oos_executed_ev": ex_ev,
        "oos_executed_w": ex_w,
        "oos_executed_n": ex_n,
        "oos_executed_p": ex_p,
        "is_executed_ev": is_ex_ev,
        "is_executed_n": is_ex_n,
        "degradation": degradation,
        "fee_breakeven_w": fee_be,
        "gate1": gate1,
        "gate2": gate2,
        "verdict": "pass" if gate2 else ("conditional" if gate1 else "fail"),
        "splits": {"theoretical": split_th, "executed": split_ex},
    }


def pick_best(results: list[dict], key: str = "oos_executed_p") -> dict | None:
    valid = [r for r in results if r.get(key) is not None and not np.isnan(r.get(key))]
    return max(valid, key=lambda r: r[key]) if valid else None


def pick_best_gate1(results: list[dict]) -> dict | None:
    g1 = [r for r in results if r.get("gate1")]
    return pick_best(g1) if g1 else None
