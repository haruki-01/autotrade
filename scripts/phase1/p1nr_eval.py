"""P1-NR evaluation helpers: N × RR × R with theoretical + executed."""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import GATE2_P_TARGET, filter_df_by_split
from scripts.phase1.metrics import fee_breakeven_win_rate, summarize_trades
from scripts.phase1.n_targets import n_band
from scripts.phase1.nr_targets import build_nr_target_row
from scripts.phase1.p1n_sensitivity import find_cooldown_for_n
from scripts.phase1.signals.h_d_pull import generate_hd_pull_signals

OOS_SPLITS = ("OOS1", "OOS2")


@dataclass
class NRConfig:
    n_target: int
    rr_ratio: float
    pct_risk: float = 0.008
    atr_mult: float = 0.5
    max_bars: int = 48
    cooldown: int | None = None

    def label(self) -> str:
        cd = self.cooldown if self.cooldown is not None else "auto"
        return f"N{self.n_target}_RR{self.rr_ratio:.0f}_R{self.pct_risk}_cd{cd}"


def _signal_kwargs(cfg: NRConfig) -> dict:
    return {
        "weekend_filter": True,
        "mode": "pull",
        "cooldown": cfg.cooldown or 48,
        "pct_risk": cfg.pct_risk,
        "atr_mult": cfg.atr_mult,
        "max_bars": cfg.max_bars,
        "rr_ratio": cfg.rr_ratio,
    }


def resolve_cooldown(df, cfg: NRConfig) -> int:
    if cfg.cooldown is not None:
        return cfg.cooldown
    all_df = filter_df_by_split(df, "ALL")
    return find_cooldown_for_n(all_df, cfg.n_target)


def evaluate_config(df, cfg: NRConfig, cooldown: int | None = None) -> dict:
    cd = cooldown if cooldown is not None else resolve_cooldown(df, cfg)
    cfg_resolved = NRConfig(
        n_target=cfg.n_target,
        rr_ratio=cfg.rr_ratio,
        pct_risk=cfg.pct_risk,
        atr_mult=cfg.atr_mult,
        max_bars=cfg.max_bars,
        cooldown=cd,
    )
    target = build_nr_target_row(cfg.n_target, cfg.rr_ratio, cfg.pct_risk)
    band_low, band_high = n_band(cfg.n_target)
    sig_kw = _signal_kwargs(cfg_resolved)

    split_th, split_ex = {}, {}
    for split in OOS_SPLITS:
        sub = filter_df_by_split(df, split)
        sigs = generate_hd_pull_signals(sub, **sig_kw)
        th_trades = run_backtest(sub, sigs, apply_execution=False)
        ex_trades = run_backtest(sub, sigs, apply_execution=True)
        split_th[split] = summarize_trades(th_trades, sub, "theoretical_pnl")
        split_ex[split] = summarize_trades(ex_trades, sub, "executed_pnl")

    def _avg(key: str, src: dict, attr: str) -> float:
        vals = [src[s].get(attr) for s in OOS_SPLITS if src[s].get(attr) is not None]
        return float(np.mean(vals)) if vals else float("nan")

    th_ev = _avg("th", split_th, "ev")
    ex_ev = _avg("ex", split_ex, "ev")
    ex_w = _avg("ex", split_ex, "w")
    ex_n = _avg("ex", split_ex, "monthly_n")
    ex_p = _avg("ex", split_ex, "p")
    th_p = _avg("th", split_th, "p")
    degradation = ex_ev / th_ev if th_ev and not np.isnan(th_ev) and th_ev != 0 else float("nan")

    gate1 = ex_ev > 0 and band_low <= ex_n <= band_high
    gate2 = ex_p >= GATE2_P_TARGET
    w_check = ex_w >= target["w_star_gate2"] if not np.isnan(ex_w) else False
    fee_be = fee_breakeven_win_rate(cfg.pct_risk, cfg.pct_risk * cfg.rr_ratio)

    return {
        "config": asdict(cfg_resolved),
        "label": cfg_resolved.label(),
        "target": target,
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
