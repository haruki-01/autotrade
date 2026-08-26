"""Map a prepared slow-strategy bar to an intent. Same rules as the BT engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Intent:
    logic_id: str
    bar_time: pd.Timestamp
    action: str  # flat | enter_long | enter_short | exit_long | exit_short
    stop_pct: float | None
    tp_pct: float | None
    close: float
    in_position_side: str | None


def last_complete_bar(frame: pd.DataFrame, now: pd.Timestamp, bar_minutes: int = 15) -> pd.Series:
    """Drop the in-progress candle. Signal is on a *closed* 15m bar."""
    if frame.empty:
        raise ValueError("empty frame")
    last_ts = pd.Timestamp(frame.index[-1])
    if last_ts.tzinfo is None:
        last_ts = last_ts.tz_localize("UTC")
    close_at = last_ts + pd.Timedelta(minutes=bar_minutes)
    use = frame.iloc[:-1] if now < close_at else frame
    if use.empty:
        raise ValueError("no complete bar yet")
    return use.iloc[-1]


def intent_for_bar(
    logic_id: str,
    row: pd.Series,
    *,
    position_side: str | None,
) -> Intent:
    ts = pd.Timestamp(row.name)
    close = float(row["close"])
    stop = float(row["stop_pct"]) if "stop_pct" in row.index else None
    if "tp_pct" in row.index and pd.notna(row["tp_pct"]):
        tp = float(row["tp_pct"])
    else:
        tp = None

    if position_side == "long" and bool(row.get("structure_exit_long", False)):
        return Intent(logic_id, ts, "exit_long", stop, tp, close, position_side)
    if position_side == "short" and bool(row.get("structure_exit_short", False)):
        return Intent(logic_id, ts, "exit_short", stop, tp, close, position_side)
    if position_side is not None:
        return Intent(logic_id, ts, "flat", stop, tp, close, position_side)
    if bool(row.get("long_signal", False)):
        return Intent(logic_id, ts, "enter_long", stop, tp, close, None)
    if bool(row.get("short_signal", False)):
        return Intent(logic_id, ts, "enter_short", stop, tp, close, None)
    return Intent(logic_id, ts, "flat", stop, tp, close, None)
