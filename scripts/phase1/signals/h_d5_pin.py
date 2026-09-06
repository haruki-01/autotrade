"""H-D5: 12h pin bar crowd fade / continuation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features, resample_ohlc
from scripts.phase1.common import (
    HD_CANONICAL_MAX_BARS,
    HD_CANONICAL_SL_PCT,
    HD_CANONICAL_TP_PCT,
    Signal,
)


def pin_12h_events(df: pd.DataFrame) -> list[tuple[int, int]]:
    """
    Detect 12h pin bars mapped to last 5m bar in the 12h window.
    Returns list of (bar_idx, direction) where direction = pin bias:
      +1 bullish pin (long lower wick), -1 bearish pin (long upper wick).
    """
    h12 = resample_ohlc(df, "12h")
    events: list[tuple[int, int]] = []
    for _, bar in h12.iterrows():
        body = abs(bar["close"] - bar["open"])
        rng = bar["high"] - bar["low"]
        if rng == 0 or body == 0:
            continue
        upper = bar["high"] - max(bar["open"], bar["close"])
        lower = min(bar["open"], bar["close"]) - bar["low"]
        direction = 0
        if upper >= 2 * body:
            direction = -1
        elif lower >= 2 * body:
            direction = 1
        if direction == 0:
            continue
        t = bar["open_time"]
        match = df.loc[(df["open_time"] >= t) & (df["open_time"] < t + pd.Timedelta(hours=12))]
        if match.empty:
            continue
        events.append((int(match.index[-1]), direction))
    return events


def generate_hd5_signals(
    df: pd.DataFrame,
    mode: str = "fade",
    entry_mode: str = "pull",
    weekend_filter: bool = True,
    cooldown: int = 48,
    sl_pct: float = HD_CANONICAL_SL_PCT,
    tp_pct: float = HD_CANONICAL_TP_PCT,
    max_bars: int = HD_CANONICAL_MAX_BARS,
) -> list[Signal]:
    """
    mode: fade = trade against pin crowd (Phase0 weak-positive).
          cont = trade with pin direction (control).
    entry_mode: immediate = pin bar close; pull = best price in next 6 bars.
    """
    df = add_features(df)
    trade_dir_sign = -1 if mode == "fade" else 1
    signals: list[Signal] = []
    last_bar = -cooldown

    for bar_idx, pin_dir in pin_12h_events(df):
        if bar_idx <= last_bar + cooldown:
            continue
        if weekend_filter and df["is_weekend"].iloc[bar_idx]:
            continue

        direction = pin_dir * trade_dir_sign

        if entry_mode == "pull" and bar_idx + 6 < len(df):
            window = df.iloc[bar_idx + 1 : bar_idx + 7]
            if window.empty:
                continue
            if direction == 1:
                entry_i = int(window["low"].idxmin())
            else:
                entry_i = int(window["high"].idxmax())
        else:
            entry_i = bar_idx

        entry = float(df["close"].iloc[entry_i])
        if direction == 1:
            sl = entry * (1 - sl_pct)
            tp = entry * (1 + tp_pct)
        else:
            sl = entry * (1 + sl_pct)
            tp = entry * (1 - tp_pct)

        signals.append(
            Signal(
                bar_idx=entry_i,
                direction=direction,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp,
                max_bars=max_bars,
                tag=f"hd5_{mode}_{entry_mode}",
            )
        )
        last_bar = entry_i

    return signals


def expected_monthly_events(df: pd.DataFrame) -> float:
    from scripts.phase1.common import months_in_df

    n = len(pin_12h_events(df))
    return n / months_in_df(df)
