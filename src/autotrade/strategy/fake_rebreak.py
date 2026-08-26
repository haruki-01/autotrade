"""D-001 composite: compression → failed break → real rebreak / retest."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from autotrade.indicators import atr, donchian_high, donchian_low
from autotrade.strategy.common import merge_series_asof, norm_ohlcv


@dataclass
class FakeRebreakParams:
    entry_window: int = 20
    exit_window: int = 10
    atr_period: int = 14
    compress_mult: float = 0.75
    compress_lookback: int = 10
    compress_min_days: int = 3
    fail_window: int = 5
    stop_atr_mult: float = 2.0
    min_stop_pct: float = 0.5
    # retest mode
    retest_tol_atr: float = 0.5
    retest_max_days: int = 8


def _true_range(h: pd.Series, l: pd.Series, c: pd.Series) -> pd.Series:
    prev = c.shift(1)
    return pd.concat([(h - l), (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)


def _daily_setup(d: pd.DataFrame, p: FakeRebreakParams) -> pd.DataFrame:
    d = d.copy()
    d["dc_hi"] = donchian_high(d["high"], p.entry_window)
    d["dc_lo"] = donchian_low(d["low"], p.entry_window)
    d["dc_exit_lo"] = donchian_low(d["low"], p.exit_window)
    d["daily_atr"] = atr(d["high"], d["low"], d["close"], p.atr_period)
    tr = _true_range(d["high"], d["low"], d["close"])
    atr_pct = (tr.rolling(p.atr_period).mean() / d["close"]).replace(0, np.nan)
    d["atr_pct"] = atr_pct
    d["atr_pct_sma"] = atr_pct.rolling(20).mean()
    d["compressed"] = d["atr_pct"] < d["atr_pct_sma"] * p.compress_mult
    recent_comp = (
        d["compressed"].rolling(p.compress_lookback).sum() >= p.compress_min_days
    )
    d["recent_compress"] = recent_comp.fillna(False)

    # Break relative to prior bar's Donchian high (no look-ahead)
    prior_hh = d["dc_hi"].shift(1)
    d["break_up"] = d["close"] > prior_hh
    d["up_sig"] = d["break_up"] & ~d["break_up"].shift(1).fillna(False)
    d["exit_long"] = d["close"] < d["dc_exit_lo"]

    n = len(d)
    fail_arm = np.zeros(n, dtype=bool)
    rebreak_sig = np.zeros(n, dtype=bool)
    retest_armed_level = np.full(n, np.nan)
    break_level_mem = np.nan
    fail_deadline = -1
    awaiting_fail = False
    armed = False
    armed_level = np.nan
    retest_deadline = -1

    closes = d["close"].to_numpy(dtype=float)
    up_sig = d["up_sig"].fillna(False).to_numpy()
    recent = d["recent_compress"].to_numpy()
    atrs = d["daily_atr"].to_numpy(dtype=float)

    for i in range(n):
        if awaiting_fail and i <= fail_deadline:
            if closes[i] < break_level_mem:
                armed = True
                armed_level = break_level_mem
                awaiting_fail = False
                fail_arm[i] = True
        elif awaiting_fail and i > fail_deadline:
            awaiting_fail = False

        if up_sig[i] and recent[i] and not armed and not awaiting_fail:
            # First break after compression — do not enter; wait for fail
            awaiting_fail = True
            break_level_mem = float(prior_hh.iloc[i]) if pd.notna(prior_hh.iloc[i]) else closes[i]
            fail_deadline = i + p.fail_window
            continue

        if up_sig[i] and armed:
            # Real rebreak
            rebreak_sig[i] = True
            retest_armed_level[i] = armed_level
            retest_deadline = i + p.retest_max_days
            armed = False
            armed_level = np.nan
            continue

        if armed:
            retest_armed_level[i] = armed_level

        # Keep retest level visible for a few days after rebreak for mode2
        if i > 0 and np.isnan(retest_armed_level[i]) and not np.isnan(retest_armed_level[i - 1]):
            if i <= retest_deadline:
                retest_armed_level[i] = retest_armed_level[i - 1]

    d["fail_arm"] = fail_arm
    d["rebreak_sig"] = rebreak_sig
    d["retest_level"] = retest_armed_level
    d["prior_hh"] = prior_hh
    return d


def prepare_frames_rebreak(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: FakeRebreakParams | None = None,
) -> pd.DataFrame:
    """Empirical ①: enter on rebreak day (first bar) + H4 confirm."""
    params = params or FakeRebreakParams()
    d = _daily_setup(norm_ohlcv(daily), params)
    h = norm_ohlcv(h4)
    h["h4_confirm"] = h["close"] > h["open"]
    m = norm_ohlcv(m15)

    merged = merge_series_asof(
        m,
        d,
        ["rebreak_sig", "exit_long", "daily_atr", "retest_level"],
        shift=pd.Timedelta(days=1),
    )
    merged = merge_series_asof(
        merged, h, ["h4_confirm"], shift=pd.Timedelta(hours=4)
    )
    day = merged.index.floor("D")
    first_bar = ~pd.Series(day, index=merged.index).duplicated(keep="first")
    merged["long_signal"] = (
        merged["rebreak_sig"].fillna(False)
        & first_bar
        & merged["h4_confirm"].fillna(False)
    )
    merged["short_signal"] = False
    return _exits(merged, params)


def prepare_frames_retest(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: FakeRebreakParams | None = None,
) -> pd.DataFrame:
    """Empirical ②: after rebreak, buy support retest of break level."""
    params = params or FakeRebreakParams()
    d = _daily_setup(norm_ohlcv(daily), params)
    # Mark days after rebreak while retest_level is live
    d["post_rebreak"] = d["retest_level"].notna() & ~d["rebreak_sig"].fillna(False)

    h = norm_ohlcv(h4)
    h["h4_bull"] = h["close"] > h["open"]
    m = norm_ohlcv(m15)

    merged = merge_series_asof(
        m,
        d,
        ["post_rebreak", "retest_level", "exit_long", "daily_atr", "rebreak_sig"],
        shift=pd.Timedelta(days=1),
    )
    merged = merge_series_asof(merged, h, ["h4_bull"], shift=pd.Timedelta(hours=4))

    level = merged["retest_level"]
    atr_v = merged["daily_atr"]
    tol = atr_v * params.retest_tol_atr
    near = (merged["low"] <= level + tol) & (merged["high"] >= level - tol)
    bounce = merged["close"] > merged["open"]
    # One entry per calendar day max
    day = merged.index.floor("D")
    first_hit = near & bounce & merged["post_rebreak"].fillna(False) & merged["h4_bull"].fillna(
        False
    )
    # de-dupe to first bar of day that qualifies
    eligible = first_hit.fillna(False)
    picked = eligible & ~pd.Series(day, index=merged.index).where(eligible).duplicated(keep="first")
    # avoid same day as rebreak signal mapped bars
    merged["long_signal"] = picked & ~merged["rebreak_sig"].fillna(False)
    merged["short_signal"] = False
    return _exits(merged, params)


def _exits(merged: pd.DataFrame, params: FakeRebreakParams) -> pd.DataFrame:
    atr_pct = (
        merged["daily_atr"] / merged["close"] * 100.0 * params.stop_atr_mult
    ).clip(lower=params.min_stop_pct)
    merged["atr"] = merged["daily_atr"]
    merged["stop_pct"] = atr_pct.fillna(params.min_stop_pct)
    merged["tp_pct"] = float("nan")
    merged["trail_atr_mult"] = float("nan")
    merged["structure_exit_long"] = merged["exit_long"].fillna(False)
    merged["structure_exit_short"] = False
    merged["h4_long_break"] = False
    merged["h4_short_break"] = False
    merged["daily_against_long"] = False
    merged["daily_against_short"] = False
    return merged
