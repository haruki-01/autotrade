"""H-C2: weekly gap (Mon open vs Fri close) continuation signals."""

from __future__ import annotations

import pandas as pd

from scripts.phase0.b07_metrics import week_open_events
from scripts.phase1.common import (
    HD_CANONICAL_MAX_BARS,
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    Signal,
    months_in_df,
)


def generate_hc2_signals(
    df: pd.DataFrame,
    mode: str = "cont",
    min_gap_pct: float = 0.0,
    min_gap_abs: float | None = None,
    sl_pct: float = HD_CANONICAL_SL_PCT,
    tp_pct: float = HD_CANONICAL_TP_PCT,
    max_bars: int = HD_CANONICAL_MAX_BARS,
) -> list[Signal]:
    """
    mode: cont = gap direction (H-C2), revert = against gap (control).
    min_gap_pct: minimum |gap| as fraction (e.g. 0.005 = 0.5%).
    min_gap_abs: optional absolute gap threshold (overrides min_gap_pct when set).
    """
    gaps = week_open_events(df)
    if gaps.empty:
        return []

    signals: list[Signal] = []
    for _, row in gaps.iterrows():
        gap_abs = float(row["gap_abs"])
        if min_gap_abs is not None:
            if gap_abs < min_gap_abs:
                continue
        elif gap_abs < min_gap_pct:
            continue

        direction = int(row["gap_dir"])
        if mode == "revert":
            direction = -direction

        i = int(row["bar_i"])
        entry = float(df["open"].iloc[i])
        if direction == 1:
            sl = entry * (1 - sl_pct)
            tp = entry * (1 + tp_pct)
        else:
            sl = entry * (1 + sl_pct)
            tp = entry * (1 - tp_pct)

        signals.append(
            Signal(
                bar_idx=i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=f"hc2_{mode}",
            )
        )

    return signals


def expected_monthly_events(df: pd.DataFrame, min_gap_pct: float = 0.0) -> float:
    gaps = week_open_events(df)
    if gaps.empty:
        return 0.0
    if min_gap_pct > 0:
        gaps = gaps[gaps["gap_abs"] >= min_gap_pct]
    months = months_in_df(df)
    return len(gaps) / months
