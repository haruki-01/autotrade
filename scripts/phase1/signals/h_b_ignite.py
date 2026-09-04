"""H-B: IGNITE momentum signals (early / pull / late)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, detect_ignite
from scripts.phase1.common import RR_RATIO, Signal

LATE_MOVE_PCT = 0.015  # H-M5: skip if already +1.5% from streak start
PULL_MIN_RETRACE = 0.20
PULL_MAX_RETRACE = 0.40
PULL_LOOKAHEAD = 12


def _streak_start_price(df: pd.DataFrame, i: int, direction: int) -> float:
    if i >= 2:
        return float(df["open"].iloc[i - 2])
    return float(df["close"].iloc[i])


def _move_from_start(df: pd.DataFrame, i: int, direction: int, price: float) -> float:
    start = _streak_start_price(df, i, direction)
    if start <= 0:
        return 0.0
    if direction == 1:
        return (price - start) / start
    return (start - price) / start


def _pullback_ok(df: pd.DataFrame, i: int, direction: int) -> bool:
    """SPEC: close-based retracement during ignition < 30% of extension."""
    if i < 2:
        return True
    start = _streak_start_price(df, i, direction)
    end = float(df["close"].iloc[i])
    if direction == 1:
        ext = end - start
        if ext <= 0:
            return False
        running_high = start
        max_pull = 0.0
        for j in range(i - 2, i + 1):
            c = float(df["close"].iloc[j])
            running_high = max(running_high, c)
            max_pull = max(max_pull, running_high - c)
        return max_pull / ext < 0.30
    ext = start - end
    if ext <= 0:
        return False
    running_low = start
    max_pull = 0.0
    for j in range(i - 2, i + 1):
        c = float(df["close"].iloc[j])
        running_low = min(running_low, c)
        max_pull = max(max_pull, c - running_low)
    return max_pull / ext < 0.30


def _find_pull_entry(df: pd.DataFrame, ignite_i: int, direction: int) -> int | None:
    start = _streak_start_price(df, ignite_i, direction)
    peak = start
    for j in range(ignite_i + 1, min(ignite_i + 1 + PULL_LOOKAHEAD, len(df))):
        row = df.iloc[j]
        if direction == 1:
            peak = max(peak, float(row["high"]))
            move = peak - start
            if move <= 0 or (peak - start) / max(start, 1) < 0.005:
                continue
            retrace = (peak - float(row["close"])) / move
        else:
            peak = min(peak, float(row["low"]))
            move = start - peak
            if move <= 0 or (start - peak) / max(start, 1) < 0.005:
                continue
            retrace = (float(row["close"]) - peak) / move
        if PULL_MIN_RETRACE <= retrace <= PULL_MAX_RETRACE:
            return j
    return None


def generate_hb_signals(
    df: pd.DataFrame,
    mode: str = "early",
    weekend_filter: bool = False,
    late_entry_ban: bool = True,
    cooldown: int = 48,
    pct_risk: float = 0.010,
    atr_mult: float = 0.5,
    rr_ratio: float | None = None,
    max_bars: int = 48,
    session_filter: str | None = None,
) -> list[Signal]:
    """
    mode: early = ignite bar entry, pull = 20-40% retrace, late = +1.5% move entry (control).
    """
    rr = rr_ratio if rr_ratio is not None else RR_RATIO
    df = add_features(df)
    df = detect_ignite(df)
    signals: list[Signal] = []
    last_bar = -cooldown

    ignite_bars = df.index[df["is_ignite"]].tolist()
    for idx in ignite_bars:
        i = df.index.get_loc(idx)
        direction = int(df["ignite_dir"].iloc[i])
        if direction == 0:
            continue

        if mode == "late":
            # Control: enter on late condition (+1.5% move after ignite)
            window = df.iloc[i + 1 : i + 1 + 48]
            entry_i = None
            start = _streak_start_price(df, i, direction)
            peak = start
            for j, (_, row) in enumerate(window.iterrows()):
                bar_i = i + 1 + j
                if direction == 1:
                    peak = max(peak, float(row["high"]))
                    if (peak - start) / start >= LATE_MOVE_PCT:
                        entry_i = bar_i
                        break
                else:
                    peak = min(peak, float(row["low"]))
                    if (start - peak) / start >= LATE_MOVE_PCT:
                        entry_i = bar_i
                        break
            if entry_i is None:
                continue
        elif mode == "pull":
            entry_i = _find_pull_entry(df, i, direction)
            if entry_i is None:
                continue
        else:
            entry_i = i

        if entry_i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[entry_i]:
            continue
        if session_filter and df["session"].iloc[entry_i] != session_filter:
            continue
        if mode in ("early", "pull") and not _pullback_ok(df, i, direction):
            continue
        if late_entry_ban and mode != "late":
            move = _move_from_start(df, entry_i, direction, float(df["close"].iloc[entry_i]))
            if move >= LATE_MOVE_PCT:
                continue

        entry = float(df["close"].iloc[entry_i])
        atr = df["atr14"].iloc[entry_i]
        if np.isnan(atr) or atr <= 0:
            continue
        r = max(entry * pct_risk, atr_mult * atr)
        sl = entry - r if direction == 1 else entry + r
        tp = entry + rr * r if direction == 1 else entry - rr * r

        signals.append(
            Signal(
                bar_idx=entry_i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=f"hb_{mode}",
            )
        )
        last_bar = entry_i

    return signals
