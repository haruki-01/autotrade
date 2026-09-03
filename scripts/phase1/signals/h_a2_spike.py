"""H-A2: SPIKE continuation signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features
from scripts.phase1.common import Signal


def generate_ha2_signals(
    df: pd.DataFrame,
    weekend_filter: bool = False,
    cooldown: int = 12,
    mode: str = "cont",
) -> list[Signal]:
    """
    mode: cont = spike direction (H-A2), revert = against spike (H-A control).
    """
    df = add_features(df)
    signals: list[Signal] = []
    last_bar = -cooldown

    for i in range(len(df)):
        if not df["is_spike"].iloc[i]:
            continue
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue

        direction = int(df["spike_dir"].iloc[i])
        if direction == 0:
            continue
        if mode == "revert":
            direction = -direction

        entry = float(df["close"].iloc[i])
        atr = df["atr14"].iloc[i]
        if np.isnan(atr) or atr <= 0:
            continue
        sl_dist = 0.3 * atr
        tp_dist = 0.6 * atr

        if direction == 1:
            sl, tp = entry - sl_dist, entry + tp_dist
        else:
            sl, tp = entry + sl_dist, entry - tp_dist

        signals.append(
            Signal(
                bar_idx=i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=12,
                tag="ha2_cont" if mode == "cont" else "ha_revert",
            )
        )
        last_bar = i

    return signals
