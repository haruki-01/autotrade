"""SPEC §7.3 execution model for Phase1 backtests."""

from __future__ import annotations

import numpy as np

from scripts.phase1.common import (
    LEV_FEE_DAILY,
    LIMIT_ENTRY_FILL,
    LIMIT_TP_FILL,
    MARKET_SLIP,
    POSITION_Q,
    TRADE_FEE,
    Signal,
    Trade,
    crosses_lev_fee_window,
)


def _lev_cost(entry_time, exit_time) -> float:
    return POSITION_Q * LEV_FEE_DAILY * crosses_lev_fee_window(entry_time, exit_time)


def theoretical_pnl(direction: int, entry: float, exit_price: float, entry_time, exit_time) -> tuple[float, float]:
    ret = direction * (exit_price / entry - 1)
    pnl = POSITION_Q * ret - POSITION_Q * TRADE_FEE * 2 - _lev_cost(entry_time, exit_time)
    return pnl, ret


def executed_pnl(
    direction: int,
    entry: float,
    exit_price: float,
    exit_reason: str,
    entry_time,
    exit_time,
    rng: np.random.Generator,
) -> tuple[float, float, bool]:
    """Apply fill/slip rules. Returns (pnl, ret, filled)."""
    if rng.random() > LIMIT_ENTRY_FILL:
        return 0.0, 0.0, False

    slip_in = MARKET_SLIP
    eff_entry = entry * (1 + slip_in * direction)

    if exit_reason == "tp" and rng.random() > LIMIT_TP_FILL:
        exit_reason = "timeout_market"

    slip_out = 0.0 if exit_reason == "tp" else MARKET_SLIP
    eff_exit = exit_price * (1 - slip_out * direction)

    ret = direction * (eff_exit / eff_entry - 1)
    pnl = POSITION_Q * ret - POSITION_Q * TRADE_FEE * 2 - _lev_cost(entry_time, exit_time)
    return pnl, ret, True


def simulate_trade(
    df,
    sig: Signal,
    rng: np.random.Generator,
    apply_execution: bool,
) -> Trade:
    i = sig.bar_idx
    entry_time = df["open_time"].iloc[i]
    entry = sig.entry_price
    direction = sig.direction
    exit_bar = i
    exit_price = entry
    reason = "timeout"

    for j in range(i + 1, min(i + 1 + sig.max_bars, len(df))):
        row = df.iloc[j]
        if direction == 1:
            if row["low"] <= sig.sl_price:
                exit_bar, exit_price, reason = j, sig.sl_price, "sl"
                break
            if row["high"] >= sig.tp_price:
                exit_bar, exit_price, reason = j, sig.tp_price, "tp"
                break
        else:
            if row["high"] >= sig.sl_price:
                exit_bar, exit_price, reason = j, sig.sl_price, "sl"
                break
            if row["low"] <= sig.tp_price:
                exit_bar, exit_price, reason = j, sig.tp_price, "tp"
                break
        exit_bar = j
        exit_price = row["close"]

    if reason == "timeout" and exit_bar == i:
        exit_bar = min(i + sig.max_bars, len(df) - 1)
        exit_price = df["close"].iloc[exit_bar]

    exit_time = df["open_time"].iloc[exit_bar]
    th_pnl, th_ret = theoretical_pnl(direction, entry, exit_price, entry_time, exit_time)

    if apply_execution:
        ex_pnl, ex_ret, filled = executed_pnl(direction, entry, exit_price, reason, entry_time, exit_time, rng)
        if not filled:
            return Trade(sig, False, exit_bar, exit_price, "no_fill", 0.0, 0.0, 0.0, 0.0)
        return Trade(sig, True, exit_bar, exit_price, reason, th_pnl, ex_pnl, th_ret, ex_ret)

    return Trade(sig, True, exit_bar, exit_price, reason, th_pnl, th_pnl, th_ret, th_ret)
