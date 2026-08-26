"""Parameterized H4 / multi-condition spot logics for hypothesis cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from autotrade.indicators import atr, donchian_high, donchian_low, sma
from autotrade.strategy.common import merge_series_asof, norm_ohlcv


@dataclass
class SpotParams:
    hh: int = 20
    exit_hh: int = 10
    atr_period: int = 14
    sma_period: int = 50
    stop_atr_mult: float = 2.0
    min_stop_pct: float = 0.5
    expand_mult: float = 1.25
    compress_mult: float = 0.75
    near_high_q: float = 0.85
    near_low_q: float = 0.15
    pb_lo: float = -0.08
    pb_hi: float = -0.02
    half_lo: float = -0.06
    half_hi: float = -0.03


def _h4_features(h4: pd.DataFrame, p: SpotParams) -> pd.DataFrame:
    h = norm_ohlcv(h4).copy()
    c, hi, lo, o = h["close"], h["high"], h["low"], h["open"]
    h["hh"] = donchian_high(hi, p.hh)
    h["ll"] = donchian_low(lo, p.hh)
    h["exit_lo"] = donchian_low(lo, p.exit_hh)
    h["exit_hi"] = donchian_high(hi, p.exit_hh)
    h["atr"] = atr(hi, lo, c, p.atr_period)
    h["sma"] = sma(c, p.sma_period)
    h["above_sma"] = c > h["sma"]
    h["sma_up"] = h["sma"] > h["sma"].shift(5)

    prev = c.shift(1)
    tr = pd.concat([(hi - lo), (hi - prev).abs(), (lo - prev).abs()], axis=1).max(axis=1)
    atr_pct = tr.rolling(p.atr_period).mean() / c
    atr_sma = atr_pct.rolling(20).mean()
    h["compressed"] = atr_pct < atr_sma * p.compress_mult
    h["expanded"] = atr_pct > atr_sma * p.expand_mult

    rng = (h["hh"] - h["ll"]).replace(0, np.nan)
    h["pos"] = (c - h["ll"]) / rng
    h["near_high"] = h["pos"] > p.near_high_q
    h["near_low"] = h["pos"] < p.near_low_q
    prior_hh = h["hh"].shift(1)
    prior_ll = h["ll"].shift(1)
    h["break_hh"] = c > prior_hh
    h["break_ll"] = c < prior_ll
    h["up_sig"] = h["break_hh"] & ~h["break_hh"].shift(1).fillna(False)
    h["dn_sig"] = h["break_ll"] & ~h["break_ll"].shift(1).fillna(False)
    h["dd"] = c / h["hh"] - 1.0
    h["shallow_pb"] = (h["dd"] > p.pb_lo) & (h["dd"] < p.pb_hi)
    h["half_pb"] = (h["dd"] > p.half_lo) & (h["dd"] < p.half_hi)
    h["bull"] = c > o
    h["bear"] = c < o

    ts = h.index
    hour = ts.hour
    h["asia"] = (hour >= 0) & (hour <= 6)
    h["london"] = (hour >= 7) & (hour <= 15)
    h["ny"] = (hour >= 13) & (hour <= 20)
    h["ny_overlap"] = (hour >= 13) & (hour <= 16)
    h["not_asia"] = ~h["asia"]
    return h


def _daily_features(daily: pd.DataFrame, p: SpotParams) -> pd.DataFrame:
    d = norm_ohlcv(daily).copy()
    c, hi, lo = d["close"], d["high"], d["low"]
    d["hh"] = donchian_high(hi, p.hh)
    d["ll"] = donchian_low(lo, p.hh)
    d["exit_lo"] = donchian_low(lo, p.exit_hh)
    d["exit_hi"] = donchian_high(hi, p.exit_hh)
    d["atr"] = atr(hi, lo, c, p.atr_period)
    d["sma"] = sma(c, p.sma_period)
    d["above_sma"] = c > d["sma"]
    d["sma_up"] = d["sma"] > d["sma"].shift(5)
    prior_hh = d["hh"].shift(1)
    prior_ll = d["ll"].shift(1)
    d["break_hh"] = c > prior_hh
    d["break_ll"] = c < prior_ll
    d["up_sig"] = d["break_hh"] & ~d["break_hh"].shift(1).fillna(False)
    d["dn_sig"] = d["break_ll"] & ~d["break_ll"].shift(1).fillna(False)
    rng = (d["hh"] - d["ll"]).replace(0, np.nan)
    d["pos"] = (c - d["ll"]) / rng
    d["near_high"] = d["pos"] > p.near_high_q
    prev = c.shift(1)
    tr = pd.concat([(hi - lo), (hi - prev).abs(), (lo - prev).abs()], axis=1).max(axis=1)
    atr_pct = tr.rolling(p.atr_period).mean() / c
    atr_sma = atr_pct.rolling(20).mean()
    d["expanded"] = atr_pct > atr_sma * p.expand_mult
    d["compressed"] = atr_pct < atr_sma * p.compress_mult
    d["dd"] = c / d["hh"] - 1.0
    d["deep_pb"] = d["dd"] < -0.12
    d["shallow_pb"] = (d["dd"] > -0.08) & (d["dd"] < -0.02)
    # second break approx: up_sig and had a break_hh in prior 10 days that failed
    failed = (hi.shift(1) > prior_hh.shift(1)) & (c.shift(1) < prior_hh.shift(1))
    d["second_break"] = d["up_sig"] & failed.rolling(10).max().fillna(False).astype(bool)
    # reclaim after deep pb: was deep, now new high
    d["reclaim_after_deep"] = d["deep_pb"].shift(1).fillna(False).rolling(15).max().astype(bool) & d["up_sig"]
    return d


SetupFn = Callable[[pd.DataFrame, pd.DataFrame, SpotParams], pd.Series]


def _finish(
    m15: pd.DataFrame,
    long_sig: pd.Series,
    short_sig: pd.Series,
    atr_s: pd.Series,
    exit_long: pd.Series,
    exit_short: pd.Series,
    p: SpotParams,
) -> pd.DataFrame:
    merged = m15.copy()
    merged["long_signal"] = long_sig.fillna(False)
    merged["short_signal"] = short_sig.fillna(False)
    atr_pct = (atr_s / merged["close"] * 100.0 * p.stop_atr_mult).clip(lower=p.min_stop_pct)
    merged["atr"] = atr_s
    merged["stop_pct"] = atr_pct.fillna(p.min_stop_pct)
    merged["tp_pct"] = float("nan")
    merged["trail_atr_mult"] = float("nan")
    merged["structure_exit_long"] = exit_long.fillna(False)
    merged["structure_exit_short"] = exit_short.fillna(False)
    merged["h4_long_break"] = False
    merged["h4_short_break"] = False
    merged["daily_against_long"] = False
    merged["daily_against_short"] = False
    return merged


def _first_of_bucket(index: pd.DatetimeIndex, freq: str) -> pd.Series:
    bucket = index.floor(freq)
    return ~pd.Series(bucket, index=index).duplicated(keep="first")


def prepare_h4_rule(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    rule: str,
    params: SpotParams | None = None,
) -> pd.DataFrame:
    p = params or SpotParams()
    h = _h4_features(h4, p)
    d = _daily_features(daily, p)
    m = norm_ohlcv(m15)

    # rule → boolean on H4 index
    rules: dict[str, pd.Series] = {
        "h4_break_non_asia": h["up_sig"] & h["not_asia"] & h["above_sma"],
        "h4_break_london": h["up_sig"] & h["london"] & h["above_sma"],
        "h4_break_ny": h["up_sig"] & h["ny_overlap"] & h["above_sma"],
        "h4_break_asia_only": h["up_sig"] & h["asia"] & h["above_sma"],  # adversary / expect weak
        "h4_shallow_pb_exp": h["shallow_pb"] & h["expanded"] & h["above_sma"] & h["bull"],
        "h4_half_pb_london": h["half_pb"] & h["above_sma"] & h["sma_up"] & h["london"] & h["bull"],
        "h4_bm_entry": h["near_high"] & h["up_sig"] & h["bull"],
        "h4_near_high_exp_london": h["near_high"] & h["expanded"] & h["london"] & h["above_sma"],
        "h4_fail_ll_reclaim_london": (
            h["break_ll"].shift(1).fillna(False)
            & (h["close"] > h["ll"].shift(1))
            & h["above_sma"]
            & h["london"]
            & h["bull"]
        ),
        "h4_fail_ll_reclaim_ny": (
            h["break_ll"].shift(1).fillna(False)
            & (h["close"] > h["ll"].shift(1))
            & h["above_sma"]
            & h["ny_overlap"]
            & h["bull"]
        ),
        "h4_compress_break_london": (
            h["compressed"].shift(1).fillna(False) & h["up_sig"] & h["london"] & h["above_sma"]
        ),
        "h4_dn_break_not_asia": h["dn_sig"] & h["not_asia"] & (~h["above_sma"]),  # short
        "h4_fade_near_high_asia": h["near_high"] & h["asia"] & h["bear"],  # short fade
        "h4_expanded_trend_cont": h["expanded"] & h["above_sma"] & h["bull"] & h["near_high"] & h["not_asia"],
        "h4_pb_after_up_sig": (
            h["up_sig"].shift(1).fillna(False).rolling(6).max().astype(bool)
            & h["shallow_pb"]
            & h["bull"]
            & h["above_sma"]
            & h["not_asia"]
        ),
        "h4_two_bull_near_high": h["near_high"] & h["bull"] & h["bull"].shift(1).fillna(False) & h["above_sma"] & h["not_asia"],
        "h4_break_below_sma_long": h["up_sig"] & (~h["above_sma"]) & h["not_asia"],  # counter-trend break
        "h4_low_reclaim_bull": (
            h["near_low"].shift(1).fillna(False) & h["bull"] & h["above_sma"] & h["london"]
        ),
        "h4_range_mid_break_up": (h["pos"].shift(1) < 0.5) & h["up_sig"] & h["not_asia"],
        "h4_repeat_break": (
            (h["up_sig"].shift(1).rolling(18).sum() >= 1) & h["up_sig"] & h["not_asia"] & h["above_sma"]
        ),
        "h4_first_break_only": (
            h["up_sig"] & (h["up_sig"].shift(1).rolling(18).sum() == 0) & h["not_asia"] & h["above_sma"]
        ),
        "h4_shallow_pb_exp_london": (
            h["shallow_pb"] & h["expanded"] & h["london"] & h["above_sma"] & h["bull"]
        ),
        "h4_shallow_pb_exp_ny": (
            h["shallow_pb"] & h["expanded"] & h["ny_overlap"] & h["above_sma"] & h["bull"]
        ),
        "h4_bm_not_asia": h["near_high"] & h["up_sig"] & h["bull"] & h["not_asia"],
        "h4_break_non_asia_exp": h["up_sig"] & h["not_asia"] & h["expanded"] & h["above_sma"],
        "h4_break_non_asia_comp": h["up_sig"] & h["not_asia"] & h["compressed"] & h["above_sma"],
        "h4_break_midweek": h["up_sig"]
        & h["not_asia"]
        & h["above_sma"]
        & pd.Series(h.index.weekday, index=h.index).isin([1, 2, 3]),
        "h4_inside_bar_break": (
            ((h["high"] < h["high"].shift(1)) & (h["low"] > h["low"].shift(1))).shift(1).fillna(False)
            & h["up_sig"]
            & h["not_asia"]
            & h["above_sma"]
        ),
        "h4_break_bull_confirm": h["up_sig"] & h["not_asia"] & h["above_sma"] & h["bull"],
    }
    if rule not in rules:
        raise ValueError(f"Unknown h4 rule: {rule}")

    sig = rules[rule].fillna(False)
    short_rules = {"h4_dn_break_not_asia", "h4_fade_near_high_asia"}
    is_short = rule in short_rules

    cols = ["atr", "exit_lo", "exit_hi"]
    h_sig = h.copy()
    h_sig["rule_sig"] = sig
    merged = merge_series_asof(m, h_sig, cols + ["rule_sig"], shift=pd.Timedelta(hours=4))
    merged = merge_series_asof(
        merged,
        d.rename(
            columns={
                "above_sma": "d_above",
                "up_sig": "d_up",
                "second_break": "d_second",
                "reclaim_after_deep": "d_reclaim",
                "exit_lo": "d_exit_lo",
                "expanded": "d_exp",
                "near_high": "d_near",
                "shallow_pb": "d_shallow",
                "atr": "d_atr",
            }
        ),
        [
            "d_above",
            "d_up",
            "d_second",
            "d_reclaim",
            "d_exit_lo",
            "d_exp",
            "d_near",
            "d_shallow",
            "d_atr",
        ],
        shift=pd.Timedelta(days=1),
    )

    first4 = _first_of_bucket(merged.index, "4h")
    fire = merged["rule_sig"].fillna(False) & first4
    if is_short:
        long_sig = pd.Series(False, index=merged.index)
        short_sig = fire
        exit_long = pd.Series(False, index=merged.index)
        exit_short = (merged["close"] > merged["exit_hi"]).fillna(False) & first4
    else:
        long_sig = fire
        short_sig = pd.Series(False, index=merged.index)
        exit_long = (merged["close"] < merged["exit_lo"]).fillna(False) & first4
        exit_short = pd.Series(False, index=merged.index)

    return _finish(merged, long_sig, short_sig, merged["atr"], exit_long, exit_short, p)


def prepare_daily_rule(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    rule: str,
    params: SpotParams | None = None,
) -> pd.DataFrame:
    p = params or SpotParams()
    d = _daily_features(daily, p)
    h = _h4_features(h4, p)
    m = norm_ohlcv(m15)

    rules: dict[str, pd.Series] = {
        "d_second_break": d["second_break"] & d["above_sma"],
        "d_reclaim_deep": d["reclaim_after_deep"] & d["above_sma"],
        "d_break_not_compress": d["up_sig"] & (~d["compressed"]) & d["above_sma"],
        "d_shallow_pb": d["shallow_pb"] & d["above_sma"] & d["sma_up"],
        "d_near_high_exp": d["near_high"] & d["expanded"] & d["above_sma"],  # known fail twin — skip in cycles
        "d_half_pb": (d["dd"] > -0.06) & (d["dd"] < -0.03) & d["above_sma"] & d["sma_up"],
        "d_break_any_sma": d["up_sig"],  # no sma filter — frequency
        "d_dn_break_below_sma": d["dn_sig"] & (~d["above_sma"]),
        "d_exp_break": d["up_sig"] & d["expanded"] & d["above_sma"],
        "d_comp_break": d["up_sig"] & d["compressed"] & d["above_sma"],
        "d_near_high_break": d["up_sig"] & d["near_high"],
    }
    wd = pd.Series(d.index.weekday, index=d.index)
    rules["d_monday_break"] = d["up_sig"] & d["above_sma"] & (wd == 0)
    rules["d_fri_break"] = d["up_sig"] & d["above_sma"] & (wd == 4)
    if rule not in rules:
        raise ValueError(f"Unknown daily rule: {rule}")

    short_rules = {"d_dn_break_below_sma"}
    is_short = rule in short_rules
    d2 = d.copy()
    d2["rule_sig"] = rules[rule].fillna(False)
    h2 = h.copy()
    h2["h4_bull"] = h["bull"]

    merged = merge_series_asof(
        m, d2, ["rule_sig", "atr", "exit_lo", "exit_hi"], shift=pd.Timedelta(days=1)
    )
    merged = merge_series_asof(merged, h2, ["h4_bull"], shift=pd.Timedelta(hours=4))
    first = _first_of_bucket(merged.index, "D")
    fire = merged["rule_sig"].fillna(False) & first & merged["h4_bull"].fillna(False)
    if is_short:
        fire = merged["rule_sig"].fillna(False) & first & (~merged["h4_bull"].fillna(True))
        long_sig = pd.Series(False, index=merged.index)
        short_sig = fire
        exit_long = pd.Series(False, index=merged.index)
        exit_short = (merged["close"] > merged["exit_hi"]).fillna(False) & first
    else:
        long_sig = fire
        short_sig = pd.Series(False, index=merged.index)
        exit_long = (merged["close"] < merged["exit_lo"]).fillna(False) & first
        exit_short = pd.Series(False, index=merged.index)
    return _finish(merged, long_sig, short_sig, merged["atr"], exit_long, exit_short, p)


# logic_id → (family, rule, hypothesis_id, name)
CYCLE_LOGICS: dict[str, tuple[str, str, str, str]] = {
    # Cycle 1 — R4H / BM
    "h4_break_non_asia_v1": ("h4", "h4_break_non_asia", "HYP-012", "R4H-001 アジア外4H突破"),
    "h4_break_london_v1": ("h4", "h4_break_london", "HYP-013", "R4H-003 ロンドン4H突破"),
    "h4_shallow_pb_exp_v1": ("h4", "h4_shallow_pb_exp", "HYP-014", "R4H-002 浅い押し×拡大"),
    "h4_bm_entry_v1": ("h4", "h4_bm_entry", "HYP-015", "R-BM-001 伸び入口"),
    "h4_half_pb_london_v1": ("h4", "h4_half_pb_london", "HYP-016", "R4H-004 半値押しロンドン"),
    # Cycle 2 — session contrast + NY + fail reclaim
    "h4_break_ny_v1": ("h4", "h4_break_ny", "HYP-017", "NY重なり4H突破"),
    "h4_break_asia_only_v1": ("h4", "h4_break_asia_only", "HYP-018", "アジアのみ突破（対照）"),
    "h4_fail_ll_reclaim_v1": ("h4", "h4_fail_ll_reclaim_london", "HYP-019", "D-004系 失敗下抜け回復"),
    "h4_near_high_exp_lon_v1": ("h4", "h4_near_high_exp_london", "HYP-020", "高値拡大ロンドン"),
    # Cycle 3 — continuation / post-break pb
    "h4_pb_after_break_v1": ("h4", "h4_pb_after_up_sig", "HYP-021", "突破後の浅い押し"),
    "h4_exp_trend_cont_v1": ("h4", "h4_expanded_trend_cont", "HYP-022", "拡大トレンド継続"),
    "h4_compress_break_lon_v1": ("h4", "h4_compress_break_london", "HYP-023", "圧縮後ロンドン突破"),
    "d_second_break_v1": ("daily", "d_second_break", "HYP-024", "D-002 二度目突破"),
    # Cycle 4 — daily reclaim / frequency
    "d_reclaim_deep_v1": ("daily", "d_reclaim_deep", "HYP-025", "D-003 深押し取り戻し"),
    "d_break_not_compress_v1": ("daily", "d_break_not_compress", "HYP-026", "非圧縮日足突破"),
    "d_shallow_pb_v1": ("daily", "d_shallow_pb", "HYP-027", "日足浅い押し"),
    "d_half_pb_v1": ("daily", "d_half_pb", "HYP-028", "日足半値押し"),
    # Cycle 5 — shorts / fade
    "h4_dn_break_non_asia_v1": ("h4", "h4_dn_break_not_asia", "HYP-029", "アジア外下抜けショート"),
    "h4_fade_asia_high_v1": ("h4", "h4_fade_near_high_asia", "HYP-030", "アジア高値フェード短"),
    "d_dn_break_v1": ("daily", "d_dn_break_below_sma", "HYP-031", "日足下抜けショート"),
    "d_break_any_v1": ("daily", "d_break_any_sma", "HYP-032", "日足突破（フィルタ薄）"),
    # Cycle 6 — weekday / vol regime breaks
    "d_monday_break_v1": ("daily", "d_monday_break", "HYP-033", "月曜突破"),
    "d_fri_break_v1": ("daily", "d_fri_break", "HYP-034", "金曜突破"),
    "d_exp_break_v1": ("daily", "d_exp_break", "HYP-035", "拡大中の突破"),
    "d_comp_break_v1": ("daily", "d_comp_break", "HYP-036", "圧縮中の突破"),
    # Cycle 7 — repeat vs first break, mid-range
    "h4_repeat_break_v1": ("h4", "h4_repeat_break", "HYP-037", "4H再突破"),
    "h4_first_break_v1": ("h4", "h4_first_break_only", "HYP-038", "4H初回突破のみ"),
    "h4_mid_range_break_v1": ("h4", "h4_range_mid_break_up", "HYP-039", "レンジ中位からの突破"),
    "h4_two_bull_high_v1": ("h4", "h4_two_bull_near_high", "HYP-040", "高値帯連陽"),
    # Cycle 8 — reclaim / counter / low bounce
    "h4_low_reclaim_v1": ("h4", "h4_low_reclaim_bull", "HYP-041", "安値帯からの陽線回復"),
    "h4_break_below_sma_v1": ("h4", "h4_break_below_sma_long", "HYP-042", "SMA下での上抜け"),
    "d_near_high_break_v1": ("daily", "d_near_high_break", "HYP-043", "高値帯での日足突破"),
    "h4_break_bull_confirm_v1": ("h4", "h4_break_bull_confirm", "HYP-052", "非アジア突破＋陽線確認"),
    # Cycle 9 — session-narrowed / vol-split
    "h4_shallow_pb_exp_lon_v1": ("h4", "h4_shallow_pb_exp_london", "HYP-044", "浅い押し拡大×ロンドン"),
    "h4_shallow_pb_exp_ny_v1": ("h4", "h4_shallow_pb_exp_ny", "HYP-045", "浅い押し拡大×NY"),
    "h4_bm_not_asia_v1": ("h4", "h4_bm_not_asia", "HYP-046", "伸び入口×非アジア"),
    "h4_break_non_asia_exp_v1": ("h4", "h4_break_non_asia_exp", "HYP-047", "非アジア×拡大突破"),
    # Cycle 10 — structure / calendar / compression contrast
    "h4_break_non_asia_comp_v1": ("h4", "h4_break_non_asia_comp", "HYP-048", "非アジア×圧縮突破"),
    "h4_break_midweek_v1": ("h4", "h4_break_midweek", "HYP-049", "火水木の非アジア突破"),
    "h4_inside_bar_break_v1": ("h4", "h4_inside_bar_break", "HYP-050", "インサイドバー後突破"),
    "h4_fail_ll_reclaim_ny_v1": ("h4", "h4_fail_ll_reclaim_ny", "HYP-051", "失敗下抜け回復×NY"),
}


def prepare_cycle_logic(
    logic_id: str,
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
) -> pd.DataFrame:
    if logic_id not in CYCLE_LOGICS:
        raise ValueError(f"Unknown cycle logic: {logic_id}")
    family, rule, _, _ = CYCLE_LOGICS[logic_id]
    if family == "h4":
        return prepare_h4_rule(daily, h4, m15, rule)
    return prepare_daily_rule(daily, h4, m15, rule)
