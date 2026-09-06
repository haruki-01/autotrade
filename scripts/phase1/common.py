"""Phase1 shared constants and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

INITIAL_BANKROLL = 50_000
MARGIN_RATIO = 0.10  # margin = B * MARGIN_RATIO
POSITION_Q = INITIAL_BANKROLL // 5  # Q = 2 * margin = B/5 (SPEC §2)
RR_RATIO = 2.0

# H-D canonical exit (P1-R2 VALIDATION best, locked for P1-R2C+)
HD_CANONICAL_SL_PCT = 0.005
HD_CANONICAL_TP_PCT = 0.010
HD_CANONICAL_MAX_BARS = 48
HD_CANONICAL_COOLDOWN = 48

N_TARGET = 50
N_BAND_LOW = 40
N_BAND_HIGH = 60
GATE2_PCT = 0.05
GATE2_P_TARGET = int(INITIAL_BANKROLL * GATE2_PCT)  # 2_500 JPY/month

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

# Hybrid validation aliases (validation-spec.md)
SPLIT_ALIASES = {
    "TRAIN": "IS",
    "VALIDATION": "OOS1",
    "TEST": "OOS2",
}

RESEARCH_GATE_PF_MIN = 1.15
RESEARCH_GATE_DD_MAX = INITIAL_BANKROLL * 0.15  # 15% of BR
RESEARCH_GATE_WF_PASS_RATE = 0.60
RESEARCH_GATE_MC_DD_P95_MAX = INITIAL_BANKROLL * 0.15
RESEARCH_GATE_MC_RUIN_MAX = 0.05


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
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    mfe_jpy: float = 0.0
    mae_jpy: float = 0.0


def resolve_split(split: str) -> str:
    return SPLIT_ALIASES.get(split, split)


def filter_df_by_split(df: pd.DataFrame, split: str) -> pd.DataFrame:
    split = resolve_split(split)
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
