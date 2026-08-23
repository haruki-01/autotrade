"""SPOT-001 double-bottom → neckline break → neckline bounce (no EMA)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from autotrade.indicators import atr
from autotrade.strategy.common import merge_series_asof, norm_ohlcv

BounceMode = Literal[
    "bullish_close",
    "reclaim_extension",
    "pct_of_height",
    "fixed_pct",
    "break_bounce_high",
]
BreakMode = Literal["close", "wick", "clean_atr"]
StopMode = Literal["neck", "second_bottom", "atr"]
StructTF = Literal["1h", "4h", "1d"]
HtfFilter = Literal["none", "up_only", "not_down"]


@dataclass
class DoubleBottomParams:
    structure_tf: StructTF = "4h"
    pivot_left: int = 3
    pivot_right: int = 3
    bottom_tol_atr: float = 0.6
    min_bars_between: int = 6
    max_bars_between: int = 60
    break_mode: BreakMode = "close"
    clean_break_atr: float = 0.25
    retest_band_atr: float = 0.5
    bounce_mode: BounceMode = "bullish_close"
    bounce_fixed_pct: float = 0.003
    bounce_height_frac: float = 0.5
    retest_max_bars_after_break: int | None = None
    first_retest_only: bool = False
    htf_filter: HtfFilter = "none"
    stop_mode: StopMode = "neck"
    stop_atr_mult: float = 1.5
    min_stop_pct: float = 0.4
    trail_atr_mult: float | None = None
    long_only: bool = True
    enable_short_mirror: bool = False
    session_lon_ny_only: bool = False
    atr_period: int = 14


def _resample_ohlcv(m15: pd.DataFrame, rule: str) -> pd.DataFrame:
    o = m15["open"].resample(rule).first()
    h = m15["high"].resample(rule).max()
    l = m15["low"].resample(rule).min()
    c = m15["close"].resample(rule).last()
    v = m15["volume"].resample(rule).sum() if "volume" in m15.columns else None
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c})
    if v is not None:
        out["volume"] = v
    return out.dropna(subset=["open", "high", "low", "close"])


def _pivot_lows(low: pd.Series, left: int, right: int) -> pd.Series:
    n = len(low)
    vals = low.to_numpy(dtype=float)
    out = np.full(n, np.nan)
    for i in range(left, n - right):
        window = vals[i - left : i + right + 1]
        if np.isnan(window).any():
            continue
        if vals[i] == np.min(window):
            out[i] = vals[i]
    return pd.Series(out, index=low.index)


def _pivot_highs(high: pd.Series, left: int, right: int) -> pd.Series:
    n = len(high)
    vals = high.to_numpy(dtype=float)
    out = np.full(n, np.nan)
    for i in range(left, n - right):
        window = vals[i - left : i + right + 1]
        if np.isnan(window).any():
            continue
        if vals[i] == np.max(window):
            out[i] = vals[i]
    return pd.Series(out, index=high.index)


def _htf_structure_bias(d: pd.DataFrame) -> pd.Series:
    """Higher-high / higher-low vs lower-high / lower-low (no EMA)."""
    pl = _pivot_lows(d["low"], 2, 2)
    ph = _pivot_highs(d["high"], 2, 2)
    bias = pd.Series("range", index=d.index, dtype=object)
    last_lo: list[float] = []
    last_hi: list[float] = []
    for i in range(len(d)):
        if np.isfinite(pl.iloc[i]):
            last_lo.append(float(pl.iloc[i]))
            if len(last_lo) > 3:
                last_lo = last_lo[-3:]
        if np.isfinite(ph.iloc[i]):
            last_hi.append(float(ph.iloc[i]))
            if len(last_hi) > 3:
                last_hi = last_hi[-3:]
        if len(last_lo) >= 2 and len(last_hi) >= 2:
            up = last_lo[-1] > last_lo[-2] and last_hi[-1] > last_hi[-2]
            dn = last_lo[-1] < last_lo[-2] and last_hi[-1] < last_hi[-2]
            if up:
                bias.iloc[i] = "up"
            elif dn:
                bias.iloc[i] = "down"
            else:
                bias.iloc[i] = "range"
        elif i > 0:
            bias.iloc[i] = bias.iloc[i - 1]
    return bias


def _detect_long_patterns(s: pd.DataFrame, p: DoubleBottomParams) -> pd.DataFrame:
    """Scan all double-bottom → break → retest-bounce events on structure TF."""
    n = len(s)
    atr_s = atr(s["high"], s["low"], s["close"], p.atr_period).to_numpy(dtype=float)
    low = s["low"].to_numpy(dtype=float)
    high = s["high"].to_numpy(dtype=float)
    close = s["close"].to_numpy(dtype=float)
    open_ = s["open"].to_numpy(dtype=float)
    piv = _pivot_lows(s["low"], p.pivot_left, p.pivot_right).to_numpy(dtype=float)

    long_sig = np.zeros(n, dtype=bool)
    neck_arr = np.full(n, np.nan)
    stop_pct = np.full(n, np.nan)
    struct_exit = np.zeros(n, dtype=bool)

    pivot_idx = [i for i in range(n) if np.isfinite(piv[i])]
    used_entry_bars: set[int] = set()

    for i in pivot_idx:
        a_i = atr_s[i]
        if not np.isfinite(a_i) or a_i <= 0:
            continue
        candidates = [
            j
            for j in pivot_idx
            if p.min_bars_between <= (i - j) <= p.max_bars_between
        ]
        chosen = None
        for j in reversed(candidates):
            if abs(piv[i] - piv[j]) <= p.bottom_tol_atr * a_i:
                neck_cand = float(np.max(high[j : i + 1]))
                if neck_cand > max(piv[i], piv[j]) * 1.001:
                    chosen = (j, neck_cand)
                    break
        if chosen is None:
            continue
        j, neck = chosen
        b1, b2 = float(piv[j]), float(piv[i])
        height = neck - min(b1, b2)
        if height <= 0:
            continue
        floor = min(b1, b2)

        # First break after second bottom
        break_i = -1
        break_ext = np.nan
        search_end = n if p.retest_max_bars_after_break is None else min(n, i + 1 + 120)
        for k in range(i + 1, search_end):
            if close[k] < floor:
                break  # pattern dead
            a_k = atr_s[k]
            if not np.isfinite(a_k):
                continue
            broke = False
            if p.break_mode == "close":
                broke = close[k] > neck
            elif p.break_mode == "wick":
                broke = high[k] > neck
            elif p.break_mode == "clean_atr":
                broke = close[k] > neck + p.clean_break_atr * a_k
            if broke:
                break_i = k
                break_ext = float(high[k])
                break
        if break_i < 0:
            continue

        retest_deadline = n
        if p.retest_max_bars_after_break is not None:
            retest_deadline = min(n, break_i + 1 + p.retest_max_bars_after_break)

        touched = False
        pending_entry_break = False
        bounce_high = np.nan
        for k in range(break_i + 1, retest_deadline):
            if close[k] < floor:
                break
            a_k = atr_s[k]
            if not np.isfinite(a_k) or a_k <= 0:
                continue
            if close[k] < neck - 0.75 * a_k:
                break  # failed retest / trend cancel
            band = p.retest_band_atr * a_k
            in_band = low[k] <= neck + band and high[k] >= neck - band
            if in_band:
                if p.first_retest_only and touched:
                    continue
                touched = True
                bounce_high = high[k] if not np.isfinite(bounce_high) else max(bounce_high, high[k])

            if not touched:
                continue

            confirm = False
            if p.bounce_mode == "bullish_close":
                confirm = close[k] > open_[k] and close[k] >= neck
            elif p.bounce_mode == "reclaim_extension":
                confirm = np.isfinite(break_ext) and close[k] > break_ext
            elif p.bounce_mode == "pct_of_height":
                confirm = close[k] >= neck + height * p.bounce_height_frac
            elif p.bounce_mode == "fixed_pct":
                confirm = close[k] >= neck * (1.0 + p.bounce_fixed_pct)
            elif p.bounce_mode == "break_bounce_high":
                if not pending_entry_break and close[k] > open_[k] and close[k] >= neck:
                    pending_entry_break = True
                    bounce_high = high[k]
                elif pending_entry_break and np.isfinite(bounce_high) and close[k] > bounce_high:
                    confirm = True

            if confirm and k not in used_entry_bars:
                long_sig[k] = True
                neck_arr[k] = neck
                if p.stop_mode == "second_bottom":
                    stop_px = floor
                    stop_pct[k] = max((close[k] - stop_px) / close[k] * 100.0, p.min_stop_pct)
                elif p.stop_mode == "neck":
                    stop_px = neck - band
                    stop_pct[k] = max((close[k] - stop_px) / close[k] * 100.0, p.min_stop_pct)
                else:
                    stop_pct[k] = max(p.stop_atr_mult * a_k / close[k] * 100.0, p.min_stop_pct)
                used_entry_bars.add(k)
                break  # one entry per DB pattern

    for i in range(5, n):
        struct_exit[i] = close[i] < np.min(low[i - 5 : i])

    out = s.copy()
    out["long_signal_raw"] = long_sig
    out["neck"] = neck_arr
    out["stop_pct_raw"] = stop_pct
    out["structure_exit_long"] = struct_exit
    out["atr_struct"] = atr_s
    return out


def _detect_short_mirror(s: pd.DataFrame, p: DoubleBottomParams) -> pd.Series:
    """Double-top → neck breakdown → bounce-fail short (mirror of long)."""
    # Flip OHLC and reuse long detector
    flip = s.copy()
    flip["high"] = -s["low"]
    flip["low"] = -s["high"]
    flip["open"] = -s["open"]
    flip["close"] = -s["close"]
    det = _detect_long_patterns(flip, p)
    return det["long_signal_raw"].fillna(False)


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: DoubleBottomParams | None = None,
) -> pd.DataFrame:
    p = params or DoubleBottomParams()
    m = norm_ohlcv(m15)
    d = norm_ohlcv(daily)
    h = norm_ohlcv(h4)

    if p.structure_tf == "1h":
        struct = _resample_ohlcv(m, "1h")
        shift = pd.Timedelta(hours=1)
    elif p.structure_tf == "1d":
        struct = d
        shift = pd.Timedelta(days=1)
    else:
        struct = h
        shift = pd.Timedelta(hours=4)

    struct = norm_ohlcv(struct)
    det = _detect_long_patterns(struct, p)

    d_bias = _htf_structure_bias(d)
    d = d.copy()
    d["daily_bias"] = d_bias

    cols = ["long_signal_raw", "stop_pct_raw", "structure_exit_long", "atr_struct", "neck"]
    merged = merge_series_asof(m, det, cols, shift=shift)
    merged = merge_series_asof(merged, d, ["daily_bias"], shift=pd.Timedelta(days=1))

    long_sig = merged["long_signal_raw"].fillna(False)
    if p.htf_filter == "up_only":
        long_sig = long_sig & (merged["daily_bias"] == "up")
    elif p.htf_filter == "not_down":
        long_sig = long_sig & (merged["daily_bias"] != "down")

    if p.session_lon_ny_only:
        hour = merged.index.hour
        # London 07–16 UTC, NY 13–21 UTC → union 07–21
        long_sig = long_sig & (hour >= 7) & (hour < 21)

    # Fire at most once per structure bar (first 15m of bucket)
    if p.structure_tf == "1h":
        bucket = merged.index.floor("1h")
    elif p.structure_tf == "1d":
        bucket = merged.index.floor("D")
    else:
        bucket = merged.index.floor("4h")
    first = ~pd.Series(bucket, index=merged.index).duplicated(keep="first")
    long_sig = long_sig & first

    merged["long_signal"] = long_sig
    if p.enable_short_mirror and not p.long_only:
        short_raw = _detect_short_mirror(struct, p)
        short_df = pd.DataFrame({"short_signal_raw": short_raw}, index=struct.index)
        merged = merge_series_asof(merged, short_df, ["short_signal_raw"], shift=shift)
        short_sig = merged["short_signal_raw"].fillna(False) & first
        if p.htf_filter == "up_only":
            short_sig = short_sig & (merged["daily_bias"] == "down")
        elif p.htf_filter == "not_down":
            short_sig = short_sig & (merged["daily_bias"] != "up")
        if p.session_lon_ny_only:
            hour = merged.index.hour
            short_sig = short_sig & (hour >= 7) & (hour < 21)
        merged["short_signal"] = short_sig
    else:
        merged["short_signal"] = False

    atr_pct = (
        merged["atr_struct"] / merged["close"] * 100.0 * p.stop_atr_mult
    ).clip(lower=p.min_stop_pct)
    stop = merged["stop_pct_raw"].where(merged["stop_pct_raw"].notna(), atr_pct)
    merged["stop_pct"] = stop.fillna(p.min_stop_pct).clip(lower=p.min_stop_pct)
    merged["tp_pct"] = float("nan")
    merged["trail_atr_mult"] = float(p.trail_atr_mult) if p.trail_atr_mult else float("nan")
    merged["atr"] = merged["atr_struct"]

    merged["structure_exit_long"] = merged["structure_exit_long"].fillna(False)
    merged["structure_exit_short"] = False
    merged["h4_long_break"] = False
    merged["h4_short_break"] = False
    merged["daily_against_long"] = merged["daily_bias"] == "down"
    merged["daily_against_short"] = merged["daily_bias"] == "up"
    return merged


# --- 20 cycle logics (1 knob each) ---

CYCLE_DB: dict[str, tuple[DoubleBottomParams, str, str]] = {
    # logic_id -> (params, hypothesis_id, name)
    "db_baseline_v1": (
        DoubleBottomParams(),
        "DB-01",
        "DB基準: 4H・終値突破・陽線反発",
    ),
    "db_htf_up_only_v1": (
        DoubleBottomParams(htf_filter="up_only"),
        "DB-02",
        "DB+日足上昇のみ",
    ),
    "db_htf_not_down_v1": (
        DoubleBottomParams(htf_filter="not_down"),
        "DB-03",
        "DB+日足下降以外",
    ),
    "db_bounce_reclaim_ext_v1": (
        DoubleBottomParams(bounce_mode="reclaim_extension"),
        "DB-04",
        "DB反発=突破高値奪還",
    ),
    "db_bounce_pct_height_v1": (
        DoubleBottomParams(bounce_mode="pct_of_height"),
        "DB-05",
        "DB反発=高の50%戻し",
    ),
    "db_bounce_fixed_pct_v1": (
        DoubleBottomParams(bounce_mode="fixed_pct"),
        "DB-06",
        "DB反発=固定0.3%",
    ),
    "db_tight_bottoms_v1": (
        DoubleBottomParams(bottom_tol_atr=0.35),
        "DB-07",
        "DB2底許容を厳しく",
    ),
    "db_wide_bottoms_v1": (
        DoubleBottomParams(bottom_tol_atr=1.0),
        "DB-08",
        "DB2底許容を緩く",
    ),
    "db_wick_break_v1": (
        DoubleBottomParams(break_mode="wick"),
        "DB-09",
        "DBヒゲ突破許可",
    ),
    "db_struct_1h_v1": (
        DoubleBottomParams(structure_tf="1h", min_bars_between=8, max_bars_between=80),
        "DB-10",
        "DB構造足=1H",
    ),
    "db_struct_daily_v1": (
        DoubleBottomParams(structure_tf="1d", min_bars_between=5, max_bars_between=40),
        "DB-11",
        "DB構造足=日足",
    ),
    "db_stop_at_bottom_v1": (
        DoubleBottomParams(stop_mode="second_bottom"),
        "DB-12",
        "DB損切=第2底",
    ),
    "db_entry_break_bounce_high_v1": (
        DoubleBottomParams(bounce_mode="break_bounce_high"),
        "DB-13",
        "DB反発足高値抜けでエントリー",
    ),
    "db_retest_fresh_v1": (
        DoubleBottomParams(retest_max_bars_after_break=12),
        "DB-14",
        "DB突破後12本以内の再テスト",
    ),
    "db_clean_break_v1": (
        DoubleBottomParams(break_mode="clean_atr"),
        "DB-15",
        "DBきれいな突破(+0.25ATR)",
    ),
    "db_first_retest_only_v1": (
        DoubleBottomParams(first_retest_only=True),
        "DB-16",
        "DB初回再テストのみ",
    ),
    "db_mirror_short_v1": (
        DoubleBottomParams(long_only=False, enable_short_mirror=True, htf_filter="none"),
        "DB-17",
        "DB対称ショート（ダブルトップ）",
    ),
    "db_session_lon_ny_v1": (
        DoubleBottomParams(session_lon_ny_only=True),
        "DB-18",
        "DBロンドン/NYのみ執行",
    ),
    "db_trail_atr_v1": (
        DoubleBottomParams(trail_atr_mult=2.5, stop_mode="atr"),
        "DB-19",
        "DB退出=ATRトレール",
    ),
    "db_1h_up_pct_height_v1": (
        DoubleBottomParams(
            structure_tf="1h",
            htf_filter="up_only",
            bounce_mode="pct_of_height",
            min_bars_between=8,
            max_bars_between=80,
        ),
        "DB-20",
        "DB事前合成: 1H×上昇×高%戻し",
    ),
}


def prepare_cycle_db(logic_id: str, daily, h4, m15) -> pd.DataFrame:
    if logic_id not in CYCLE_DB:
        raise ValueError(f"Unknown DB logic: {logic_id}")
    params, _, _ = CYCLE_DB[logic_id]
    return prepare_frames(daily, h4, m15, params)
