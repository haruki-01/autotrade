"""H-D4: pct-level crowd stop cluster (bounce / break continuation)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.b06_metrics import pct_level_events
from scripts.phase0.common import add_features
from scripts.phase1.common import (
    HD_CANONICAL_MAX_BARS,
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    RR_RATIO,
    Signal,
)


def generate_hd4_signals(
    df: pd.DataFrame,
    mode: str = "break",
    pct_level: float = -0.015,
    swing_bars: int = 24,
    entry_mode: str = "immediate",
    weekend_filter: bool = True,
    cooldown: int = 48,
    sl_pct: float | None = HD_CANONICAL_SL_PCT,
    tp_pct: float | None = HD_CANONICAL_TP_PCT,
    pct_risk: float = 0.008,
    atr_mult: float = 0.5,
    max_bars: int = HD_CANONICAL_MAX_BARS,
    rr_ratio: float | None = None,
) -> list[Signal]:
    """
    mode: bounce = long at shallow pct touch (mean reversion).
          break = short at deeper pct touch (continuation down).
    entry_mode: immediate = touch bar close; pull = min low in next 6 bars.
    """
    rr = rr_ratio if rr_ratio is not None else RR_RATIO
    df = add_features(df)
    use_fixed = sl_pct is not None and tp_pct is not None

    # Recompute events with custom swing window
    events: list[tuple[int, int]] = []
    for i in range(swing_bars, len(df)):
        swing = df["high"].iloc[i - swing_bars : i].max()
        level = swing * (1 + pct_level)
        if df["low"].iloc[i] <= level <= df["high"].iloc[i]:
            events.append((i, 1 if mode == "bounce" else -1))

    signals: list[Signal] = []
    last_bar = -cooldown

    for i, direction in events:
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue

        if entry_mode == "pull" and i + 6 < len(df):
            window = df.iloc[i + 1 : i + 7]
            if window.empty:
                continue
            if direction == 1:
                entry_i = window["low"].idxmin()
            else:
                entry_i = window["high"].idxmax()
            entry_i = df.index.get_loc(entry_i)
        else:
            entry_i = i

        entry = float(df["close"].iloc[entry_i])
        atr = df["atr14"].iloc[entry_i]
        if np.isnan(atr) or atr <= 0:
            continue

        if use_fixed:
            if direction == 1:
                sl = entry * (1 - sl_pct)
                tp = entry * (1 + tp_pct)
            else:
                sl = entry * (1 + sl_pct)
                tp = entry * (1 - tp_pct)
        else:
            r = max(entry * pct_risk, atr_mult * atr)
            if direction == 1:
                sl, tp = entry - r, entry + rr * r
            else:
                sl, tp = entry + r, entry - rr * r

        signals.append(
            Signal(
                bar_idx=entry_i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=f"hd4_{mode}",
            )
        )
        last_bar = entry_i

    return signals


def pct_touch_indices(df: pd.DataFrame, pct_level: float, swing_bars: int = 24) -> pd.Index:
    """Expose pct touch indices for preflight / diagnostics."""
    idx = []
    for i in range(swing_bars, len(df)):
        swing = df["high"].iloc[i - swing_bars : i].max()
        level = swing * (1 + pct_level)
        if df["low"].iloc[i] <= level <= df["high"].iloc[i]:
            idx.append(df.index[i])
    return pd.Index(idx)
