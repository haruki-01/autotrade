"""H-D: RSI exit oversold + first pull entry signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.b06_metrics import rsi_exit_os
from scripts.phase0.common import add_features
from scripts.phase1.common import (
    HD_CANONICAL_COOLDOWN,
    HD_CANONICAL_MAX_BARS,
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    RR_RATIO,
    Signal,
)


def canonical_hd_kwargs(**overrides) -> dict:
    """H-D + H-M4 canonical params (P1-R2C locked)."""
    base = {
        "weekend_filter": True,
        "mode": "pull",
        "sl_pct": HD_CANONICAL_SL_PCT,
        "tp_pct": HD_CANONICAL_TP_PCT,
        "max_bars": HD_CANONICAL_MAX_BARS,
        "cooldown": HD_CANONICAL_COOLDOWN,
    }
    base.update(overrides)
    return base


def generate_canonical_hd_signals(df: pd.DataFrame, **overrides) -> list[Signal]:
    return generate_hd_pull_signals(df, **canonical_hd_kwargs(**overrides))


def _risk_width(entry: float, atr: float, pct_risk: float = 0.008, atr_mult: float = 0.5) -> float:
    return max(entry * pct_risk, atr_mult * atr)


def generate_hd_pull_signals(
    df: pd.DataFrame,
    weekend_filter: bool = False,
    cooldown: int = 48,
    mode: str = "pull",
    pct_risk: float = 0.008,
    atr_mult: float = 0.5,
    max_bars: int = 48,
    rr_ratio: float | None = None,
    sl_pct: float | None = None,
    tp_pct: float | None = None,
    session_filter: str | None = None,
    avoid_fee_window: bool = False,
) -> list[Signal]:
    """
    mode: pull = wait for first pull (H-D), raw = enter on RSI exit bar (control).
    sl_pct/tp_pct: fixed percentage exits (P1-R2). Overrides R-based SL/TP when both set.
    session_filter: TOKYO | EUROPE_US | OFF — entry bar must match session.
    avoid_fee_window: skip entries in 05:30–06:30 JST (H-E lever).
    """
    rr = rr_ratio if rr_ratio is not None else RR_RATIO
    df = add_features(df)
    rsi_idx = rsi_exit_os(df)
    signals: list[Signal] = []
    last_bar = -cooldown

    for idx in rsi_idx:
        i = df.index.get_loc(idx)
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue
        if session_filter and df["session"].iloc[i] != session_filter:
            continue
        if avoid_fee_window:
            t = df["open_time"].iloc[i]
            mins = t.hour * 60 + t.minute
            if 5 * 60 + 30 <= mins <= 6 * 60 + 30:
                continue

        if mode == "raw":
            entry_i = i
        else:
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

        if sl_pct is not None and tp_pct is not None:
            sl = entry * (1 - sl_pct)
            tp = entry * (1 + tp_pct)
            tag = f"hd_{mode}_sl{sl_pct}_tp{tp_pct}"
        else:
            r = _risk_width(entry, atr, pct_risk=pct_risk, atr_mult=atr_mult)
            sl = entry - r
            tp = entry + rr * r
            tag = "hd_pull" if mode == "pull" else "hd_raw"

        signals.append(
            Signal(
                bar_idx=entry_i,
                direction=1,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=tag,
            )
        )
        last_bar = entry_i

    return signals
