"""Donchian breakout family — L-BREAK / H21 / HYP-002 / L-BREAK-2 (4H)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from autotrade.indicators import atr, donchian_high, donchian_low
from autotrade.strategy.common import merge_series_asof, norm_ohlcv


@dataclass
class DonchianParams:
    entry_window: int = 20
    exit_window: int = 10
    atr_period: int = 14
    stop_atr_mult: float = 2.0
    min_stop_pct: float = 0.5
    long_only: bool = False
    # HYP-002: first day of break streak only + 4H confirmation
    new_break_only: bool = False
    require_h4_confirm: bool = False
    # L-BREAK-2: Donchian on 4H instead of daily (sample-frequency change only)
    signal_timeframe: str = "daily"  # "daily" | "h4"


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: DonchianParams | None = None,
) -> pd.DataFrame:
    params = params or DonchianParams()
    if params.signal_timeframe == "h4":
        return _prepare_h4_signal(daily, h4, m15, params)
    return _prepare_daily_signal(daily, h4, m15, params)


def _prepare_daily_signal(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: DonchianParams,
) -> pd.DataFrame:
    d = norm_ohlcv(daily)
    d["dc_hi"] = donchian_high(d["high"], params.entry_window)
    d["dc_lo"] = donchian_low(d["low"], params.entry_window)
    d["dc_exit_lo"] = donchian_low(d["low"], params.exit_window)
    d["dc_exit_hi"] = donchian_high(d["high"], params.exit_window)
    d["daily_atr"] = atr(d["high"], d["low"], d["close"], params.atr_period)
    d["break_up"] = d["close"] > d["dc_hi"]
    d["break_down"] = d["close"] < d["dc_lo"]
    d["up_sig"] = d["break_up"] & ~d["break_up"].shift(1).fillna(False)
    d["dn_sig"] = d["break_down"] & ~d["break_down"].shift(1).fillna(False)
    d["exit_long"] = d["close"] < d["dc_exit_lo"]
    d["exit_short"] = d["close"] > d["dc_exit_hi"]

    h = norm_ohlcv(h4)
    h["h4_dc_hi"] = donchian_high(h["high"], params.entry_window)
    # Confirmed 4H bar: bullish candle OR close above 4H Donchian20
    h["h4_confirm"] = (h["close"] > h["open"]) | (h["close"] > h["h4_dc_hi"])

    m = norm_ohlcv(m15)
    daily_cols = [
        "break_up",
        "break_down",
        "up_sig",
        "dn_sig",
        "exit_long",
        "exit_short",
        "daily_atr",
    ]
    merged = merge_series_asof(
        m,
        d,
        daily_cols,
        shift=pd.Timedelta(days=1),
    )
    merged = merge_series_asof(
        merged,
        h,
        ["h4_confirm"],
        shift=pd.Timedelta(hours=4),
    )

    day = merged.index.floor("D")
    first_bar = ~pd.Series(day, index=merged.index).duplicated(keep="first")

    if params.new_break_only:
        long_base = merged["up_sig"].fillna(False)
        short_base = merged["dn_sig"].fillna(False)
    else:
        long_base = merged["break_up"].fillna(False)
        short_base = merged["break_down"].fillna(False)

    long_sig = long_base & first_bar
    short_sig = short_base & first_bar
    if params.require_h4_confirm:
        long_sig = long_sig & merged["h4_confirm"].fillna(False)
        short_sig = short_sig & merged["h4_confirm"].fillna(False)

    return _finalize_signals(merged, params, atr_col="daily_atr", long_sig=long_sig, short_sig=short_sig)


def _prepare_h4_signal(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: DonchianParams,
) -> pd.DataFrame:
    """Same 20/10 Donchian rules as L-BREAK, but computed on 4H (one change)."""
    _ = daily  # unused — intentional single-point change from daily Donchian
    h = norm_ohlcv(h4)
    h["dc_hi"] = donchian_high(h["high"], params.entry_window)
    h["dc_lo"] = donchian_low(h["low"], params.entry_window)
    h["dc_exit_lo"] = donchian_low(h["low"], params.exit_window)
    h["dc_exit_hi"] = donchian_high(h["high"], params.exit_window)
    h["h4_atr"] = atr(h["high"], h["low"], h["close"], params.atr_period)
    h["break_up"] = h["close"] > h["dc_hi"]
    h["break_down"] = h["close"] < h["dc_lo"]
    h["up_sig"] = h["break_up"] & ~h["break_up"].shift(1).fillna(False)
    h["dn_sig"] = h["break_down"] & ~h["break_down"].shift(1).fillna(False)
    h["exit_long"] = h["close"] < h["dc_exit_lo"]
    h["exit_short"] = h["close"] > h["dc_exit_hi"]

    m = norm_ohlcv(m15)
    merged = merge_series_asof(
        m,
        h,
        [
            "break_up",
            "break_down",
            "up_sig",
            "dn_sig",
            "exit_long",
            "exit_short",
            "h4_atr",
        ],
        shift=pd.Timedelta(hours=4),
    )

    # First 15m bar of each 4H bucket (mirrors daily first-bar execution)
    bucket = merged.index.floor("4h")
    first_bar = ~pd.Series(bucket, index=merged.index).duplicated(keep="first")

    if params.new_break_only:
        long_base = merged["up_sig"].fillna(False)
        short_base = merged["dn_sig"].fillna(False)
    else:
        long_base = merged["break_up"].fillna(False)
        short_base = merged["break_down"].fillna(False)

    long_sig = long_base & first_bar
    short_sig = short_base & first_bar
    return _finalize_signals(merged, params, atr_col="h4_atr", long_sig=long_sig, short_sig=short_sig)


def _finalize_signals(
    merged: pd.DataFrame,
    params: DonchianParams,
    *,
    atr_col: str,
    long_sig: pd.Series,
    short_sig: pd.Series,
) -> pd.DataFrame:
    merged["long_signal"] = long_sig
    if params.long_only:
        merged["short_signal"] = False
    else:
        merged["short_signal"] = short_sig

    atr_pct = (
        merged[atr_col] / merged["close"] * 100.0 * params.stop_atr_mult
    ).clip(lower=params.min_stop_pct)
    merged["atr"] = merged[atr_col]
    merged["stop_pct"] = atr_pct.fillna(params.min_stop_pct)
    merged["tp_pct"] = float("nan")
    merged["trail_atr_mult"] = float("nan")

    merged["structure_exit_long"] = merged["exit_long"].fillna(False)
    merged["structure_exit_short"] = merged["exit_short"].fillna(False)
    merged["h4_long_break"] = False
    merged["h4_short_break"] = False
    merged["daily_against_long"] = False
    merged["daily_against_short"] = False
    return merged
