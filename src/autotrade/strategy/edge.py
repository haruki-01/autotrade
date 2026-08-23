"""EH-01..EH-10 — hypotheses that use non-price feeds (OI / funding / basis / taker flow).

Every logic here measures on the 15m execution grid and reads derivative
context columns produced by ``autotrade.data.binance_derivatives.align_to_15m``.

Design constraints carried over from the price-only failures:

- one knob per variant (no stacking of quality filters)
- no EMA, no bar shorter than 15m
- trend families exit by ATR trail / structure, not fixed take-profit
- fade families need an explicit target, so they use an ATR-multiple target
- controls are first-class: each family ships the "filter removed" and, where
  meaningful, the "filter inverted" variant so a pass can be read as a
  difference between groups rather than a standalone number
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from autotrade.indicators import atr, donchian_high, donchian_low
from autotrade.strategy.common import norm_ohlcv

BARS_PER_HOUR = 4
BARS_PER_DAY = 96


@dataclass
class EdgeParams:
    family: str

    # --- structure / breakout
    break_window: int = BARS_PER_DAY
    exit_window: int = BARS_PER_DAY // 2

    # --- open interest
    oi_window: int = 16
    oi_thr: float = 0.005
    oi_mode: str = "up"  # up | down | any
    oi_rank_window: int = 30 * BARS_PER_DAY
    oi_rank_thr: float = 0.9

    # --- spot / perp lead-lag
    lead_window: int = 4
    lead_thr: float = 0.0005
    lead_mode: str = "spot"  # spot | perp | any
    require_momentum: bool = True

    # --- basis / premium
    prem_rank_window: int = 30 * BARS_PER_DAY
    prem_rank_thr: float = 0.9
    stall_window: int = 8
    require_stall: bool = True

    # --- funding
    trend_window: int = 4 * BARS_PER_DAY
    funding_thr: float = 0.0001
    funding_mode: str = "cheap"  # cheap | expensive | any
    reset_window: int = BARS_PER_DAY
    reset_high_thr: float = 0.0003
    # Binance BTCUSDT funding sits at the 0.01% baseline most of the time, so
    # "back to normal" means at or below that baseline, not near zero.
    reset_now_thr: float = 0.00011

    # --- positioning ratios
    div_window: int = 30 * BARS_PER_DAY
    div_thr: float = 1.0
    ratio_source: str = "sum"  # sum | count
    div_mode: str = "follow_top"  # follow_top | follow_retail
    require_tt_extreme: bool = True

    # --- OI flush
    flush_window: int = 8
    flush_thr: float = 0.01
    flush_range_mult: float = 2.0
    flush_delay: int = 2
    flush_dir: str = "resume"  # resume | fade
    pre_trend_window: int = BARS_PER_DAY

    # --- compression
    comp_rank_window: int = 30 * BARS_PER_DAY
    comp_rank_thr: float = 0.3
    comp_oi_window: int = BARS_PER_DAY
    comp_oi_thr: float = 0.01
    require_oi_build: bool = True

    # --- taker flow
    taker_window: int = 16
    taker_slope_thr: float = 0.0
    taker_mode: str = "absorb"  # absorb | confirm

    # --- refinement knobs (EH-01R / EH-07R / EH-02R families only)
    entry_mode: str = "break"  # break | confirm | retest | delay
    entry_delay: int = 0
    retest_window: int = 48
    retest_tol_atr: float = 0.5
    use_structure_exit: bool = True
    flush_trigger: str = "delay"  # delay | reclaim | oi_rebuild | stabilize
    trigger_window: int = 48
    oi_rebuild_thr: float = 0.003
    lead_measure: str = "ret_diff"  # ret_diff | cum | spread
    lead_z_window: int = 30 * BARS_PER_DAY
    lead_z_thr: float = 0.5
    gate_mode: str = "gate"  # gate | trigger
    gate_break_window: int = 48

    # --- exits / sizing
    atr_period: int = 14
    stop_atr_mult: float = 1.5
    tp_atr_mult: float | None = None
    trail_atr_mult: float | None = 2.5
    min_stop_pct: float = 0.4
    long_only: bool = False
    short_only: bool = False


# --------------------------------------------------------------------------- utils


def _pct_rank(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window=window, min_periods=max(window // 4, 20)).rank(pct=True)


def _zscore(s: pd.Series, window: int) -> pd.Series:
    m = s.rolling(window=window, min_periods=max(window // 4, 20)).mean()
    sd = s.rolling(window=window, min_periods=max(window // 4, 20)).std()
    return (s - m) / sd.replace(0.0, np.nan)


def _new_event(cond: pd.Series) -> pd.Series:
    c = cond.fillna(False).astype(bool)
    return c & ~c.shift(1).fillna(False)


def _h1_atr(m15: pd.DataFrame, period: int) -> pd.Series:
    """ATR measured on 1h bars, mapped back to 15m with a full-hour lag."""
    h1 = m15.resample("1h", label="left", closed="left").agg(
        {"high": "max", "low": "min", "close": "last"}
    )
    a = atr(h1["high"], h1["low"], h1["close"], period)
    a.index = a.index + pd.Timedelta(hours=1)
    return a.reindex(m15.index, method="ffill")


def _prior_high(m15: pd.DataFrame, window: int) -> pd.Series:
    return donchian_high(m15["high"], window)


def _prior_low(m15: pd.DataFrame, window: int) -> pd.Series:
    return donchian_low(m15["low"], window)


def _empty_signals(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["long_signal"] = False
    out["short_signal"] = False
    return out


# --------------------------------------------------------------------------- families


def _sig_oi_break(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    brk_up = f["close"] > _prior_high(f, p.break_window)
    brk_dn = f["close"] < _prior_low(f, p.break_window)
    oi_chg = f["oi"] / f["oi"].shift(p.oi_window) - 1.0
    if p.oi_mode == "up":
        oi_ok = oi_chg > p.oi_thr
    elif p.oi_mode == "down":
        oi_ok = oi_chg < -p.oi_thr
    else:
        oi_ok = pd.Series(True, index=f.index)
    return _new_event(brk_up & oi_ok), _new_event(brk_dn & oi_ok)


def _sig_spot_lead(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    spot_ret = f["close"] / f["close"].shift(p.lead_window) - 1.0
    perp_ret = f["perp_close"] / f["perp_close"].shift(p.lead_window) - 1.0
    d = spot_ret - perp_ret
    if p.lead_mode == "perp":
        lead_long, lead_short = d < -p.lead_thr, d > p.lead_thr
    elif p.lead_mode == "any":
        lead_long = lead_short = pd.Series(True, index=f.index)
    else:
        lead_long, lead_short = d > p.lead_thr, d < -p.lead_thr
    if p.require_momentum:
        lead_long = lead_long & (spot_ret > 0)
        lead_short = lead_short & (spot_ret < 0)
    return _new_event(lead_long), _new_event(lead_short)


def _sig_premium_fade(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    rank = _pct_rank(f["premium"], p.prem_rank_window)
    no_new_high = f["close"] < _prior_high(f, p.stall_window)
    no_new_low = f["close"] > _prior_low(f, p.stall_window)
    if not p.require_stall:
        no_new_high = no_new_low = pd.Series(True, index=f.index)
    short = rank > p.prem_rank_thr
    long = rank < (1.0 - p.prem_rank_thr)
    return _new_event(long & no_new_low), _new_event(short & no_new_high)


def _sig_funding_trend(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    sma = f["close"].rolling(p.trend_window, min_periods=p.trend_window).mean()
    up, dn = f["close"] > sma, f["close"] < sma
    fr = f["funding_rate"]
    if p.funding_mode == "cheap":
        ok_long, ok_short = fr <= p.funding_thr, fr >= -p.funding_thr
    elif p.funding_mode == "expensive":
        ok_long, ok_short = fr > p.funding_thr, fr < -p.funding_thr
    else:
        ok_long = ok_short = pd.Series(True, index=f.index)
    return _new_event(up & ok_long), _new_event(dn & ok_short)


def _sig_oi_peak_fail(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    oi_rank = _pct_rank(f["oi"], p.oi_rank_window)
    near_high = f["close"] > _prior_high(f, BARS_PER_DAY) * 0.99
    near_low = f["close"] < _prior_low(f, BARS_PER_DAY) * 1.01
    no_new_high = f["close"] < _prior_high(f, p.stall_window)
    no_new_low = f["close"] > _prior_low(f, p.stall_window)
    tt = f["tt_ratio"] if p.ratio_source == "sum" else f["tt_count_ratio"]
    tt_med = tt.rolling(p.div_window, min_periods=max(p.div_window // 4, 20)).median()
    crowd_long = (tt > tt_med) if p.require_tt_extreme else pd.Series(True, index=f.index)
    crowd_short = (tt < tt_med) if p.require_tt_extreme else pd.Series(True, index=f.index)
    hi = oi_rank > p.oi_rank_thr
    return (
        _new_event(hi & near_low & no_new_low & crowd_short),
        _new_event(hi & near_high & no_new_high & crowd_long),
    )


def _sig_ratio_divergence(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    tt = f["tt_ratio"] if p.ratio_source == "sum" else f["tt_count_ratio"]
    div = _zscore(f["acct_ratio"], p.div_window) - _zscore(tt, p.div_window)
    if p.div_mode == "follow_retail":
        long, short = div > p.div_thr, div < -p.div_thr
    else:
        long, short = div < -p.div_thr, div > p.div_thr
    return _new_event(long), _new_event(short)


def _sig_oi_flush(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    oi_chg = f["oi"] / f["oi"].shift(p.flush_window) - 1.0
    rng = (f["high"] - f["low"]) / f["atr_h1"]
    flush = (oi_chg < -p.flush_thr) & (rng > p.flush_range_mult)
    ev = _new_event(flush)
    shock = f["close"] / f["close"].shift(p.flush_window) - 1.0
    pre = f["close"].shift(p.flush_window) / f["close"].shift(
        p.flush_window + p.pre_trend_window
    ) - 1.0
    if p.flush_dir == "fade":
        long_dir, short_dir = shock < 0, shock > 0
    else:
        long_dir, short_dir = pre > 0, pre < 0
    long = (ev & long_dir).shift(p.flush_delay).fillna(False)
    short = (ev & short_dir).shift(p.flush_delay).fillna(False)
    return long.astype(bool), short.astype(bool)


def _sig_quiet_oi_build(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    atr_pct = f["atr_h1"] / f["close"]
    quiet = _pct_rank(atr_pct, p.comp_rank_window) < p.comp_rank_thr
    if p.require_oi_build:
        build = (f["oi"] / f["oi"].shift(p.comp_oi_window) - 1.0) > p.comp_oi_thr
        armed = quiet & build
    else:
        armed = quiet
    armed_recent = (
        armed.fillna(False).astype(float).rolling(p.comp_oi_window, min_periods=1).max() > 0
    )
    brk_up = f["close"] > _prior_high(f, p.comp_oi_window)
    brk_dn = f["close"] < _prior_low(f, p.comp_oi_window)
    return _new_event(brk_up & armed_recent), _new_event(brk_dn & armed_recent)


def _sig_taker_absorb(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    tk = f["taker_ratio"].rolling(p.taker_window, min_periods=p.taker_window).mean()
    slope = tk - tk.shift(p.taker_window)
    new_high = f["close"] > _prior_high(f, BARS_PER_DAY)
    new_low = f["close"] < _prior_low(f, BARS_PER_DAY)
    if p.taker_mode == "confirm":
        long = new_high & (slope > p.taker_slope_thr)
        short = new_low & (slope < -p.taker_slope_thr)
    else:
        long = new_low & (slope > p.taker_slope_thr)
        short = new_high & (slope < -p.taker_slope_thr)
    return _new_event(long), _new_event(short)


def _sig_funding_reset(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    sma = f["close"].rolling(p.trend_window, min_periods=p.trend_window).mean()
    fr = f["funding_rate"]
    was_high = fr.rolling(p.reset_window, min_periods=p.reset_window).max() > p.reset_high_thr
    was_low = fr.rolling(p.reset_window, min_periods=p.reset_window).min() < -p.reset_high_thr
    now_norm = fr.abs() < p.reset_now_thr
    return (
        _new_event((f["close"] > sma) & was_high & now_norm),
        _new_event((f["close"] < sma) & was_low & now_norm),
    )


SIGNAL_FNS = {
    "oi_break": _sig_oi_break,
    "spot_lead": _sig_spot_lead,
    "premium_fade": _sig_premium_fade,
    "funding_trend": _sig_funding_trend,
    "oi_peak_fail": _sig_oi_peak_fail,
    "ratio_divergence": _sig_ratio_divergence,
    "oi_flush": _sig_oi_flush,
    "quiet_oi_build": _sig_quiet_oi_build,
    "taker_absorb": _sig_taker_absorb,
    "funding_reset": _sig_funding_reset,
}

REQUIRED_COLS = {
    "oi_break": ["oi"],
    "spot_lead": ["perp_close"],
    "premium_fade": ["premium"],
    "funding_trend": ["funding_rate"],
    "oi_peak_fail": ["oi", "tt_ratio", "tt_count_ratio"],
    "ratio_divergence": ["acct_ratio", "tt_ratio", "tt_count_ratio"],
    "oi_flush": ["oi"],
    "quiet_oi_build": ["oi"],
    "taker_absorb": ["taker_ratio"],
    "funding_reset": ["funding_rate"],
}

# Families whose exit is structural (trend continuation) vs target-based (fade)
STRUCTURAL_EXIT = {"oi_break", "funding_trend", "quiet_oi_build", "funding_reset"}


def prepare_frames(
    m15: pd.DataFrame,
    deriv: pd.DataFrame,
    params: EdgeParams,
) -> pd.DataFrame:
    f = norm_ohlcv(m15)
    ctx = deriv.reindex(f.index)
    for col in ctx.columns:
        f[col] = ctx[col]

    missing = [c for c in REQUIRED_COLS[params.family] if c not in f.columns]
    if missing:
        raise RuntimeError(f"{params.family}: derivative columns missing {missing}")

    f["atr_h1"] = _h1_atr(f, params.atr_period)

    long_sig, short_sig = SIGNAL_FNS[params.family](f, params)
    if params.long_only:
        short_sig = pd.Series(False, index=f.index)
    if params.short_only:
        long_sig = pd.Series(False, index=f.index)

    f["long_signal"] = long_sig.fillna(False).astype(bool)
    f["short_signal"] = short_sig.fillna(False).astype(bool)

    f["atr"] = f["atr_h1"]
    stop_pct = (f["atr_h1"] / f["close"] * 100.0 * params.stop_atr_mult).clip(
        lower=params.min_stop_pct
    )
    f["stop_pct"] = stop_pct.fillna(params.min_stop_pct)
    if params.tp_atr_mult is None:
        f["tp_pct"] = float("nan")
    else:
        f["tp_pct"] = (f["atr_h1"] / f["close"] * 100.0 * params.tp_atr_mult).fillna(
            params.min_stop_pct * 2
        )
    f["trail_atr_mult"] = (
        float("nan") if params.trail_atr_mult is None else float(params.trail_atr_mult)
    )

    if params.family in STRUCTURAL_EXIT and params.use_structure_exit:
        f["structure_exit_long"] = (f["close"] < _prior_low(f, params.exit_window)).fillna(False)
        f["structure_exit_short"] = (f["close"] > _prior_high(f, params.exit_window)).fillna(False)
    else:
        f["structure_exit_long"] = False
        f["structure_exit_short"] = False

    f["h4_long_break"] = False
    f["h4_short_break"] = False
    f["daily_against_long"] = False
    f["daily_against_short"] = False
    return f


# --------------------------------------------------------------------------- 100 variants

_FADE = {"stop_atr_mult": 1.5, "tp_atr_mult": 2.0, "trail_atr_mult": None}
_TREND: dict[str, Any] = {"stop_atr_mult": 1.5, "tp_atr_mult": None, "trail_atr_mult": 2.5}


def _base(family: str, **kw: Any) -> EdgeParams:
    defaults = _TREND if family in STRUCTURAL_EXIT else _FADE
    return EdgeParams(family=family, **{**defaults, **kw})


def _pack(
    hyp: str,
    family: str,
    items: list[tuple[str, str, str, dict[str, Any]]],
) -> dict[str, tuple[EdgeParams, str, str, str, str]]:
    """items: (suffix, knob label, why, param overrides)"""
    base = _base(family)
    out: dict[str, tuple[EdgeParams, str, str, str, str]] = {}
    for suffix, knob, why, over in items:
        lid = f"{hyp.lower().replace('-', '')}_{suffix}"
        out[lid] = (replace(base, **over), hyp, f"{hyp} {knob}", knob, why)
    return out


CYCLE_EDGE: dict[str, tuple[EdgeParams, str, str, str, str]] = {}

CYCLE_EDGE.update(
    _pack(
        "EH-01",
        "oi_break",
        [
            ("base", "24h突破+OI増0.5%/4h", "本命。新規資金を伴う突破のみ。", {}),
            ("ctrl_no_oi", "対照: OIフィルタなし", "同じ突破を無条件で撃つ。差が出なければ仮説棄却。", {"oi_mode": "any"}),
            ("ctrl_oi_down", "対照: OI減の突破", "解消主導の突破。反対の結果が出るか。", {"oi_mode": "down"}),
            ("thr_1p0", "OI閾値1.0%", "より強い新規流入のみ。", {"oi_thr": 0.01}),
            ("thr_0p2", "OI閾値0.2%", "緩めて回数を取る。", {"oi_thr": 0.002}),
            ("oiwin_4", "OI計測1h", "短い窓の増加。", {"oi_window": 4}),
            ("oiwin_32", "OI計測8h", "長い窓の増加。", {"oi_window": 32}),
            ("brk_48", "突破12h", "頻度↑。", {"break_window": 48}),
            ("brk_192", "突破48h", "頻度↓・質↑。", {"break_window": 192}),
            ("long_only", "ロングのみ", "ショート側が足を引くかの切り分け。", {"long_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-02",
        "spot_lead",
        [
            ("base", "現物先行1h+0.05%", "本命。現金主導の初動に乗る。", {}),
            ("ctrl_no_lead", "対照: 乖離なし", "乖離条件を外す。差がなければ棄却。", {"lead_mode": "any"}),
            ("ctrl_perp_lead", "対照: 先物先行", "レバ主導側。逆の結果が出るか。", {"lead_mode": "perp"}),
            ("thr_0p10", "閾値0.10%", "より強い先行のみ。", {"lead_thr": 0.001}),
            ("thr_0p02", "閾値0.02%", "回数寄り。", {"lead_thr": 0.0002}),
            ("win_2", "計測30分", "短い先行。", {"lead_window": 2}),
            ("win_8", "計測2h", "長い先行。", {"lead_window": 8}),
            ("no_mom", "同方向確認なし", "モメンタム確認の寄与を見る。", {"require_momentum": False}),
            ("trail_1p5", "トレール1.5ATR", "早い利確側。", {"trail_atr_mult": 1.5}),
            ("long_only", "ロングのみ", "方向の切り分け。", {"long_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-03",
        "premium_fade",
        [
            ("base", "プレミアム上位10%+失速", "本命。レバ先行の上昇を売る。", {"short_only": True}),
            ("both_sides", "両側", "ディスカウント側のロングも取る。", {}),
            ("ctrl_no_stall", "対照: 失速確認なし", "確認の寄与。逆張り死の有無。", {"require_stall": False, "short_only": True}),
            ("rank_0p95", "上位5%", "より極端のみ。", {"prem_rank_thr": 0.95, "short_only": True}),
            ("rank_0p80", "上位20%", "回数寄り。", {"prem_rank_thr": 0.80, "short_only": True}),
            ("win_10d", "ランク窓10日", "短い基準。", {"prem_rank_window": 10 * BARS_PER_DAY, "short_only": True}),
            ("win_60d", "ランク窓60日", "長い基準。", {"prem_rank_window": 60 * BARS_PER_DAY, "short_only": True}),
            ("stall_24", "失速6h", "長めの失速確認。", {"stall_window": 24, "short_only": True}),
            ("tp_3atr", "利確3ATR", "目標を伸ばす。", {"tp_atr_mult": 3.0, "short_only": True}),
            ("stop_2p5", "損切2.5ATR", "踏まれ耐性。", {"stop_atr_mult": 2.5, "short_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-04",
        "funding_trend",
        [
            ("base", "4日トレンド+funding安", "本命。保有コストが安い方向のみ。", {}),
            ("ctrl_any", "対照: fundingフィルタなし", "同じトレンドを無条件で。", {"funding_mode": "any"}),
            ("ctrl_expensive", "対照: funding高", "混み合った側。逆の結果が出るか。", {"funding_mode": "expensive"}),
            ("thr_0", "閾値0（受取のみ）", "厳しい低コスト。", {"funding_thr": 0.0}),
            ("thr_0p03", "閾値0.03%", "緩い低コスト。", {"funding_thr": 0.0003}),
            ("trend_2d", "トレンド2日", "短いレジーム。", {"trend_window": 2 * BARS_PER_DAY}),
            ("trend_10d", "トレンド10日", "長いレジーム。", {"trend_window": 10 * BARS_PER_DAY}),
            ("exit_24", "構造退出24h", "遅い退出。", {"exit_window": BARS_PER_DAY}),
            ("trail_4", "トレール4ATR", "大勝ちを残す。", {"trail_atr_mult": 4.0}),
            ("long_only", "ロングのみ", "方向の切り分け。", {"long_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-05",
        "oi_peak_fail",
        [
            ("base", "OI上位10%+高値更新失敗", "本命。下に清算燃料が積まれた状態を売る。", {"short_only": True}),
            ("both_sides", "両側", "安値側のロングも取る。", {}),
            ("ctrl_no_oi", "対照: OI条件なし", "OIランクの寄与。", {"oi_rank_thr": 0.0, "short_only": True}),
            ("ctrl_no_tt", "対照: 上位比なし", "群衆偏りの寄与。", {"require_tt_extreme": False, "short_only": True}),
            ("rank_0p95", "OI上位5%", "より極端。", {"oi_rank_thr": 0.95, "short_only": True}),
            ("rank_0p80", "OI上位20%", "回数寄り。", {"oi_rank_thr": 0.80, "short_only": True}),
            ("win_10d", "OIランク窓10日", "短い基準。", {"oi_rank_window": 10 * BARS_PER_DAY, "short_only": True}),
            ("stall_24", "失速6h", "長い失速確認。", {"stall_window": 24, "short_only": True}),
            ("count_ratio", "上位比=口座数版", "比率の取り方を変える。", {"ratio_source": "count", "short_only": True}),
            ("tp_3atr", "利確3ATR", "目標を伸ばす。", {"tp_atr_mult": 3.0, "short_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-06",
        "ratio_divergence",
        [
            ("base", "個人-上位 乖離1.0σ", "本命。上位側に付く。", {}),
            ("ctrl_follow_retail", "対照: 個人側に付く", "符号を反転。逆の結果が出るか。", {"div_mode": "follow_retail"}),
            ("thr_1p5", "乖離1.5σ", "より極端のみ。", {"div_thr": 1.5}),
            ("thr_0p5", "乖離0.5σ", "回数寄り。", {"div_thr": 0.5}),
            ("win_10d", "基準窓10日", "短い基準。", {"div_window": 10 * BARS_PER_DAY}),
            ("win_60d", "基準窓60日", "長い基準。", {"div_window": 60 * BARS_PER_DAY}),
            ("count_ratio", "上位比=口座数版", "比率の取り方。", {"ratio_source": "count"}),
            ("tp_3atr", "利確3ATR", "目標を伸ばす。", {"tp_atr_mult": 3.0}),
            ("stop_2p5", "損切2.5ATR", "耐性。", {"stop_atr_mult": 2.5}),
            ("short_only", "ショートのみ", "方向の切り分け。", {"short_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-07",
        "oi_flush",
        [
            ("base", "OI急減1%/2h+大足", "本命。清算が終わった後に元方向へ。", {}),
            ("ctrl_fade", "対照: ショックをフェード", "戻り方向を反転。", {"flush_dir": "fade"}),
            ("thr_2p0", "OI急減2%", "より強い洗浄のみ。", {"flush_thr": 0.02}),
            ("thr_0p5", "OI急減0.5%", "回数寄り。", {"flush_thr": 0.005}),
            ("range_3", "値幅3ATR", "より大きなショック。", {"flush_range_mult": 3.0}),
            ("range_1p5", "値幅1.5ATR", "緩い条件。", {"flush_range_mult": 1.5}),
            ("delay_0", "遅延なし", "初動を取ろうとした場合。", {"flush_delay": 0}),
            ("delay_8", "遅延2h", "十分に待つ。", {"flush_delay": 8}),
            ("pre_48h", "元方向48h", "長い基準トレンド。", {"pre_trend_window": 2 * BARS_PER_DAY}),
            ("flushwin_16", "OI計測4h", "長い減少窓。", {"flush_window": 16}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-08",
        "quiet_oi_build",
        [
            ("base", "圧縮+OI増1%/24h", "本命。静かな仕込みの後の放れ。", {}),
            ("ctrl_no_build", "対照: OI増なし", "圧縮だけのブレイク。差が出るか。", {"require_oi_build": False}),
            ("build_2p0", "OI増2%", "より明確な仕込み。", {"comp_oi_thr": 0.02}),
            ("build_0p5", "OI増0.5%", "回数寄り。", {"comp_oi_thr": 0.005}),
            ("quiet_0p2", "圧縮下位20%", "より静かのみ。", {"comp_rank_thr": 0.2}),
            ("quiet_0p4", "圧縮下位40%", "回数寄り。", {"comp_rank_thr": 0.4}),
            ("win_48", "圧縮窓12h", "短い蓄積。", {"comp_oi_window": 48}),
            ("win_192", "圧縮窓48h", "長い蓄積。", {"comp_oi_window": 192}),
            ("trail_4", "トレール4ATR", "放れを伸ばす。", {"trail_atr_mult": 4.0}),
            ("long_only", "ロングのみ", "方向の切り分け。", {"long_only": True}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-09",
        "taker_absorb",
        [
            ("base", "高値更新+成行買い減衰", "本命。吸収されている上昇を売る。", {}),
            ("ctrl_confirm", "対照: 成行と同方向", "符号を反転（順張り）。", {"taker_mode": "confirm"}),
            ("win_8", "成行計測2h", "短い傾き。", {"taker_window": 8}),
            ("win_32", "成行計測8h", "長い傾き。", {"taker_window": 32}),
            ("slope_0p05", "傾き閾値0.05", "明確な減衰のみ。", {"taker_slope_thr": 0.05}),
            ("slope_0p15", "傾き閾値0.15", "さらに厳しく。", {"taker_slope_thr": 0.15}),
            ("tp_3atr", "利確3ATR", "目標を伸ばす。", {"tp_atr_mult": 3.0}),
            ("stop_2p5", "損切2.5ATR", "踏まれ耐性。", {"stop_atr_mult": 2.5}),
            ("short_only", "ショートのみ", "高値側だけ。", {"short_only": True}),
            ("trail_2p5", "トレール併用", "退出を伸ばす。", {"tp_atr_mult": None, "trail_atr_mult": 2.5}),
        ],
    )
)

CYCLE_EDGE.update(
    _pack(
        "EH-10",
        "funding_reset",
        [
            ("base", "funding高→平常(≤0.01%)+構造維持", "本命。混み合いが抜けた継続。", {}),
            ("ctrl_no_reset", "対照: リセット条件なし", "同じ継続を無条件で。", {"reset_high_thr": -1.0, "reset_now_thr": 1.0}),
            ("high_0p05", "事前高0.05%", "より強い混み合いから。", {"reset_high_thr": 0.0005}),
            ("high_0p02", "事前高0.02%", "弱い混み合いから。", {"reset_high_thr": 0.0002}),
            ("now_0p02", "平常0.02%まで許容", "リセット判定を緩める。", {"reset_now_thr": 0.0002}),
            ("win_2d", "参照窓2日", "短い履歴。", {"reset_window": 2 * BARS_PER_DAY}),
            ("win_5d", "参照窓5日", "長い履歴。", {"reset_window": 5 * BARS_PER_DAY}),
            ("trend_2d", "トレンド2日", "短いレジーム。", {"trend_window": 2 * BARS_PER_DAY}),
            ("trail_4", "トレール4ATR", "大勝ちを残す。", {"trail_atr_mult": 4.0}),
            ("long_only", "ロングのみ", "方向の切り分け。", {"long_only": True}),
        ],
    )
)


def prepare_cycle_edge(logic_id: str, m15: pd.DataFrame, deriv: pd.DataFrame) -> pd.DataFrame:
    params, *_ = CYCLE_EDGE[logic_id]
    return prepare_frames(m15, deriv, params)
