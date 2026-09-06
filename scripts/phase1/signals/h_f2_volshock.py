"""H-F2: VOL_SHOCK midpoint mean reversion signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, detect_vol_shock, months_in_sample
from scripts.phase1.common import RR_RATIO, Signal


def vol_shock_indices(df: pd.DataFrame) -> pd.Index:
    df = detect_vol_shock(add_features(df))
    return df.index[df["is_vol_shock"]]


def generate_hf2_mid_signals(
    df: pd.DataFrame,
    weekend_filter: bool = False,
    cooldown: int = 48,
    pct_risk: float = 0.010,
    atr_mult: float = 0.5,
    rr_ratio: float | None = None,
    max_bars: int = 24,
    mode: str = "mid",
) -> list[Signal]:
    """
    mode: mid = reversion toward shock bar midpoint (H-F2).
          cont = shock continuation control.
    """
    rr = rr_ratio if rr_ratio is not None else RR_RATIO
    df = add_features(df)
    df = detect_vol_shock(df)
    signals: list[Signal] = []
    last_bar = -cooldown

    shock_bars = df.index[df["is_vol_shock"]].tolist()
    for idx in shock_bars:
        i = df.index.get_loc(idx)
        if i <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[i]:
            continue

        row = df.iloc[i]
        mid = (float(row["high"]) + float(row["low"])) / 2
        close = float(row["close"])
        shock_dir = int(row["shock_dir"])
        if shock_dir == 0:
            continue

        if mode == "cont":
            direction = shock_dir
        else:
            if close > mid:
                direction = -1
            elif close < mid:
                direction = 1
            else:
                continue

        entry_i = i
        entry = close
        atr = row["atr14"]
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
                tag=f"hf2_{mode}",
            )
        )
        last_bar = entry_i

    return signals


def expected_monthly_events(df: pd.DataFrame) -> float:
    df = detect_vol_shock(add_features(df))
    n = int(df["is_vol_shock"].sum())
    months = months_in_sample(df)
    return n / months
