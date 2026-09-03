"""Phase1 shared constants and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

POSITION_Q = 10_000  # JPY per trade (SPEC §2)
RR_RATIO = 2.0
N_TARGET = 50
N_BAND_LOW = 40
N_BAND_HIGH = 60
GATE2_P_TARGET = 10_000  # JPY/month

LIMIT_ENTRY_FILL = 0.70
LIMIT_TP_FILL = 0.85
MARKET_SLIP = 0.0002
LEV_FEE_DAILY = 0.0004
TRADE_FEE = 0.0

RANDOM_SEED = 42
RANDOM_TRIALS = 200

SPLITS = {
    "IS": (date(2024, 1, 1), date(2025, 6, 30)),
    "OOS1": (date(2025, 7, 1), date(2026, 2, 28)),
    "OOS2": (date(2026, 3, 1), date(2026, 8, 31)),
    "ALL": (date(2024, 1, 1), date(2026, 8, 31)),
}


@dataclass
class Signal:
    bar_idx: int
    direction: int  # 1 long, -1 short
    entry_price: float
    sl_price: float
    tp_price: float
    max_bars: int
    tag: str = ""


@dataclass
class Trade:
    signal: Signal
    filled: bool
    exit_bar_idx: int
    exit_price: float
    exit_reason: str
    theoretical_pnl: float
    executed_pnl: float
    theoretical_ret: float
    executed_ret: float


def filter_df_by_split(df: pd.DataFrame, split: str) -> pd.DataFrame:
    start, end = SPLITS[split]
    ts_start = pd.Timestamp(start, tz=df["open_time"].dt.tz)
    ts_end = pd.Timestamp(end, tz=df["open_time"].dt.tz) + pd.Timedelta(hours=23, minutes=55)
    mask = (df["open_time"] >= ts_start) & (df["open_time"] <= ts_end)
    return df.loc[mask].reset_index(drop=True)


def months_in_df(df: pd.DataFrame) -> float:
    if df.empty:
        return 1.0
    days = (df["open_time"].max() - df["open_time"].min()).days
    return max(days / 30.44, 1.0)


def crosses_lev_fee_window(entry_time: pd.Timestamp, exit_time: pd.Timestamp) -> int:
    """Count JST 6:00 crossings while in position."""
    if entry_time >= exit_time:
        return 0
    count = 0
    day = entry_time.normalize()
    end_day = exit_time.normalize()
    while day <= end_day:
        boundary = day + pd.Timedelta(hours=6)
        if entry_time < boundary <= exit_time:
            count += 1
        day += pd.Timedelta(days=1)
    return count
