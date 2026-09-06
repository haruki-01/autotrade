"""H-F3: range-bound edge mean reversion signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.b09_metrics import detect_range_bound_events
from scripts.phase0.common import months_in_sample
from scripts.phase1.common import RR_RATIO, Signal


def generate_hf3_revert_signals(
    df: pd.DataFrame,
    weekend_filter: bool = False,
    cooldown: int = 48,
    pct_risk: float = 0.010,
    atr_mult: float = 0.5,
    rr_ratio: float | None = None,
    max_bars: int = 24,
    mode: str = "revert",
    range_quantile: float = 0.20,
    atr_touch_mult: float = 0.10,
    roll_bars: int = 24,
) -> list[Signal]:
    rr = rr_ratio if rr_ratio is not None else RR_RATIO
    df = detect_range_bound_events(
        df,
        range_quantile=range_quantile,
        atr_touch_mult=atr_touch_mult,
        roll_bars=roll_bars,
    )
    signals: list[Signal] = []
    last_bar = -cooldown

    event_bars = df.index[df["is_range_bound"]].tolist()
    for idx in event_bars:
        i = df.index.get_loc(idx)
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue

        rb_dir = int(df["rb_dir"].iloc[i])
        if rb_dir == 0:
            continue
        direction = rb_dir if mode == "revert" else -rb_dir

        entry = float(df["close"].iloc[i])
        atr = df["atr14"].iloc[i]
        if np.isnan(atr) or atr <= 0:
            continue
        r = max(entry * pct_risk, atr_mult * atr)
        sl = entry - r if direction == 1 else entry + r
        tp = entry + rr * r if direction == 1 else entry - rr * r

        signals.append(
            Signal(
                bar_idx=i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=f"hf3_{mode}",
            )
        )
        last_bar = i

    return signals


def expected_monthly_events(df: pd.DataFrame) -> float:
    df = detect_range_bound_events(df)
    n = int(df["is_range_bound"].sum())
    return n / months_in_sample(df)
