"""Refinement families for the three hypotheses worth developing.

The 100-cycle batch left three follow-ups, worked in this order:

1. **EH-01R** — the OI-backed breakout mechanism replicated in both periods, but
   the entry is naive (fire on the break, ATR trail). Entry *condition* is frozen;
   only exit and position construction move.
2. **EH-07R** — post-flush continuation had the right direction in both periods
   and a negative base EV, i.e. the trigger is wrong, not the idea. Rebuilt around
   what "the flush is over" actually looks like.
3. **EH-02R** — spot-leads-perp had the largest effect size of all ten and only
   39 trades. Re-measured, and used as a gate on a frequent trigger instead of
   being a trigger itself.

Families here are new names so the original 100 stay byte-for-byte reproducible.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from autotrade.strategy import edge
from autotrade.strategy.edge import (
    BARS_PER_DAY,
    EdgeParams,
    _new_event,
    _prior_high,
    _prior_low,
    _pct_rank,
    _zscore,
)


def _false(index: pd.Index) -> pd.Series:
    return pd.Series(False, index=index)


def _arm_and_trigger(
    events: pd.Series,
    trigger: pd.Series,
    window: int,
) -> pd.Series:
    """First bar where ``trigger`` holds within ``window`` bars after an event.

    One entry per event; a new event re-arms. Events are sparse (a few hundred a
    year) so the explicit loop is cheap and easier to verify than a rolling trick.
    """
    ev = events.fillna(False).to_numpy(dtype=bool)
    tg = trigger.fillna(False).to_numpy(dtype=bool)
    out = np.zeros(len(ev), dtype=bool)
    n = len(ev)
    i = 0
    while i < n:
        if not ev[i]:
            i += 1
            continue
        stop = min(i + window + 1, n)
        for j in range(i + 1, stop):
            if ev[j]:
                break
            if tg[j]:
                out[j] = True
                i = j
                break
        i += 1
    return pd.Series(out, index=events.index)


# --------------------------------------------------------------- EH-01R


def _sig_oi_break_v2(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    """Same entry condition as eh01_base. Only how we get on board changes."""
    hi, lo = _prior_high(f, p.break_window), _prior_low(f, p.break_window)
    brk_up, brk_dn = f["close"] > hi, f["close"] < lo
    oi_chg = f["oi"] / f["oi"].shift(p.oi_window) - 1.0
    if p.oi_mode == "up":
        oi_ok = oi_chg > p.oi_thr
    elif p.oi_mode == "down":
        oi_ok = oi_chg < -p.oi_thr
    else:
        oi_ok = pd.Series(True, index=f.index)

    up_ev, dn_ev = _new_event(brk_up & oi_ok), _new_event(brk_dn & oi_ok)

    if p.entry_mode == "break":
        return up_ev, dn_ev

    if p.entry_mode == "delay":
        k = max(p.entry_delay, 1)
        return up_ev.shift(k).fillna(False), dn_ev.shift(k).fillna(False)

    if p.entry_mode == "confirm":
        # The break has to still be intact one bar later.
        return (
            (up_ev.shift(1).fillna(False) & (f["close"] > hi.shift(1))),
            (dn_ev.shift(1).fillna(False) & (f["close"] < lo.shift(1))),
        )

    if p.entry_mode == "retest":
        # Come back to the broken level, hold it, then enter.
        lvl_up = hi.where(up_ev).ffill()
        lvl_dn = lo.where(dn_ev).ffill()
        tol = f["atr_h1"] * p.retest_tol_atr
        back_up = (f["low"] <= lvl_up + tol) & (f["close"] > lvl_up)
        back_dn = (f["high"] >= lvl_dn - tol) & (f["close"] < lvl_dn)
        return (
            _arm_and_trigger(up_ev, back_up, p.retest_window),
            _arm_and_trigger(dn_ev, back_dn, p.retest_window),
        )

    raise ValueError(f"unknown entry_mode: {p.entry_mode}")


# --------------------------------------------------------------- EH-07R


def _sig_oi_flush_v2(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    """Post-flush continuation. The question is when the flush is actually over."""
    oi = f["oi"]
    oi_chg = oi / oi.shift(p.flush_window) - 1.0
    rng = (f["high"] - f["low"]) / f["atr_h1"]
    flush = (oi_chg < -p.flush_thr) & (rng > p.flush_range_mult)
    ev = _new_event(flush)

    pre = f["close"].shift(p.flush_window) / f["close"].shift(
        p.flush_window + p.pre_trend_window
    ) - 1.0
    up_ev = ev & (pre > 0)
    dn_ev = ev & (pre < 0)

    if p.flush_trigger == "delay":
        k = max(p.flush_delay, 1)
        return up_ev.shift(k).fillna(False), dn_ev.shift(k).fillna(False)

    if p.flush_trigger == "stabilize":
        calm = rng < 1.0
        return (
            _arm_and_trigger(up_ev, calm, p.trigger_window),
            _arm_and_trigger(dn_ev, calm, p.trigger_window),
        )

    if p.flush_trigger == "reclaim":
        # Price has to take back the level it had before the shock.
        pre_close = f["close"].shift(p.flush_window)
        lvl_up = pre_close.where(up_ev).ffill()
        lvl_dn = pre_close.where(dn_ev).ffill()
        return (
            _arm_and_trigger(up_ev, f["close"] > lvl_up, p.trigger_window),
            _arm_and_trigger(dn_ev, f["close"] < lvl_dn, p.trigger_window),
        )

    if p.flush_trigger == "oi_rebuild":
        # Positions start being rebuilt: OI turns up off its post-flush low.
        floor = oi.rolling(p.trigger_window, min_periods=1).min()
        rebuilt = (oi / floor - 1.0) > p.oi_rebuild_thr
        return (
            _arm_and_trigger(up_ev, rebuilt, p.trigger_window),
            _arm_and_trigger(dn_ev, rebuilt, p.trigger_window),
        )

    raise ValueError(f"unknown flush_trigger: {p.flush_trigger}")


# --------------------------------------------------------------- EH-02R


def _lead_measure(f: pd.DataFrame, p: EdgeParams) -> pd.Series:
    if p.lead_measure == "cum":
        one = (f["close"].pct_change() - f["perp_close"].pct_change()).fillna(0.0)
        raw = one.rolling(p.lead_window, min_periods=p.lead_window).sum()
    elif p.lead_measure == "spread":
        spread = f["close"] / f["perp_close"] - 1.0
        raw = spread - spread.shift(p.lead_window)
    else:
        raw = (f["close"] / f["close"].shift(p.lead_window) - 1.0) - (
            f["perp_close"] / f["perp_close"].shift(p.lead_window) - 1.0
        )
    return _zscore(raw, p.lead_z_window)


def _persist(cond: pd.Series, bars: int) -> pd.Series:
    """Condition must have held for ``bars`` consecutive bars."""
    if bars <= 1:
        return cond
    held = cond.fillna(False).astype(float).rolling(bars, min_periods=bars).min() > 0
    return held


def _apply_cooldown(
    long: pd.Series, short: pd.Series, bars: int
) -> tuple[pd.Series, pd.Series]:
    """Suppress signals for ``bars`` after any signal, to cut turnover."""
    if bars <= 0:
        return long, short
    lo = long.fillna(False).to_numpy(dtype=bool).copy()
    sh = short.fillna(False).to_numpy(dtype=bool).copy()
    last = -10**9
    for i in range(len(lo)):
        if not (lo[i] or sh[i]):
            continue
        if i - last < bars:
            lo[i] = sh[i] = False
        else:
            last = i
    return pd.Series(lo, index=long.index), pd.Series(sh, index=short.index)


# --------------------------------------------------------------- EH-06R


def _sig_ratio_divergence_v2(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    """Retail-vs-top-trader divergence. The 100-cycle version traded far too often."""
    tt = f["tt_ratio"] if p.ratio_source == "sum" else f["tt_count_ratio"]
    z_acct = _zscore(f["acct_ratio"], p.div_window)
    z_tt = _zscore(tt, p.div_window)
    div = z_acct - z_tt

    if p.div_mode == "follow_retail":
        long_c, short_c = div > p.div_thr, div < -p.div_thr
    else:
        long_c, short_c = div < -p.div_thr, div > p.div_thr

    if p.both_extreme:
        # Not just a gap: each side has to be stretched on its own.
        long_c = long_c & (z_acct < 0) & (z_tt > 0)
        short_c = short_c & (z_acct > 0) & (z_tt < 0)

    long_c = _persist(long_c, p.persist_bars)
    short_c = _persist(short_c, p.persist_bars)

    if p.gate_mode == "gate":
        brk_up = f["close"] > _prior_high(f, p.gate_break_window)
        brk_dn = f["close"] < _prior_low(f, p.gate_break_window)
        long_sig = _new_event(brk_up & long_c)
        short_sig = _new_event(brk_dn & short_c)
    else:
        long_sig, short_sig = _new_event(long_c), _new_event(short_c)

    return _apply_cooldown(long_sig, short_sig, p.cooldown_bars)


# --------------------------------------------------------------- EH-09R


def _taker_ratio(f: pd.DataFrame, p: EdgeParams) -> pd.Series:
    if p.taker_source == "perp_vol":
        buy = f["perp_taker_buy"]
        sell = (f["perp_volume"] - buy).clip(lower=1e-9)
        return buy / sell
    return f["taker_ratio"]


def _sig_taker_absorb_v2(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    """New extreme in price while aggressive flow fades = absorption."""
    tk = _taker_ratio(f, p).rolling(p.taker_window, min_periods=p.taker_window).mean()
    slope = tk - tk.shift(p.taker_window)

    pad = f["atr_h1"] * p.extend_atr
    new_high = f["close"] > _prior_high(f, BARS_PER_DAY) + pad
    new_low = f["close"] < _prior_low(f, BARS_PER_DAY) - pad

    # Persistence applies to the flow condition only: a new price extreme is an
    # instant, so requiring it to hold for N bars would never fire.
    rising = _persist(slope > p.taker_slope_thr, p.persist_bars)
    falling = _persist(slope < -p.taker_slope_thr, p.persist_bars)

    if p.taker_mode == "confirm":
        long_c, short_c = new_high & rising, new_low & falling
    else:
        long_c, short_c = new_low & rising, new_high & falling

    return _apply_cooldown(_new_event(long_c), _new_event(short_c), p.cooldown_bars)


def _sig_spot_lead_v2(f: pd.DataFrame, p: EdgeParams) -> tuple[pd.Series, pd.Series]:
    """Spot-lead as a scale-free gate on a frequent trigger, not as the trigger."""
    z = _lead_measure(f, p)

    if p.lead_mode == "perp":
        gate_long, gate_short = z < -p.lead_z_thr, z > p.lead_z_thr
    elif p.lead_mode == "any":
        gate_long = gate_short = pd.Series(True, index=f.index)
    else:
        gate_long, gate_short = z > p.lead_z_thr, z < -p.lead_z_thr

    if p.gate_mode == "trigger":
        return _new_event(gate_long), _new_event(gate_short)

    brk_up = f["close"] > _prior_high(f, p.gate_break_window)
    brk_dn = f["close"] < _prior_low(f, p.gate_break_window)
    return _new_event(brk_up & gate_long), _new_event(brk_dn & gate_short)


# --------------------------------------------------------------- registration

edge.SIGNAL_FNS["oi_break_v2"] = _sig_oi_break_v2
edge.SIGNAL_FNS["oi_flush_v2"] = _sig_oi_flush_v2
edge.SIGNAL_FNS["spot_lead_v2"] = _sig_spot_lead_v2
edge.SIGNAL_FNS["ratio_divergence_v2"] = _sig_ratio_divergence_v2
edge.SIGNAL_FNS["taker_absorb_v2"] = _sig_taker_absorb_v2

edge.REQUIRED_COLS["oi_break_v2"] = ["oi"]
edge.REQUIRED_COLS["oi_flush_v2"] = ["oi"]
edge.REQUIRED_COLS["spot_lead_v2"] = ["perp_close"]
edge.REQUIRED_COLS["ratio_divergence_v2"] = ["acct_ratio", "tt_ratio", "tt_count_ratio"]
edge.REQUIRED_COLS["taker_absorb_v2"] = ["taker_ratio", "perp_taker_buy", "perp_volume"]

edge.STRUCTURAL_EXIT.add("oi_break_v2")
edge.STRUCTURAL_EXIT.add("spot_lead_v2")
# Both v2 families can run either a target exit or a structural one; the knob
# decides, so they must be eligible for structural exits.
edge.STRUCTURAL_EXIT.add("ratio_divergence_v2")
edge.STRUCTURAL_EXIT.add("taker_absorb_v2")


# --------------------------------------------------------------- variant packs

_EH01R_BASE = EdgeParams(
    family="oi_break_v2",
    break_window=BARS_PER_DAY,
    oi_window=16,
    oi_thr=0.005,
    oi_mode="up",
    stop_atr_mult=1.5,
    tp_atr_mult=None,
    trail_atr_mult=2.5,
    exit_window=BARS_PER_DAY // 2,
)

_EH07R_BASE = EdgeParams(
    family="oi_flush_v2",
    flush_window=8,
    flush_thr=0.01,
    flush_range_mult=2.0,
    pre_trend_window=BARS_PER_DAY,
    stop_atr_mult=1.5,
    tp_atr_mult=2.0,
    trail_atr_mult=None,
)

_EH02R_BASE = EdgeParams(
    family="spot_lead_v2",
    lead_window=4,
    lead_measure="ret_diff",
    lead_z_thr=0.5,
    gate_mode="gate",
    gate_break_window=48,
    stop_atr_mult=1.5,
    tp_atr_mult=None,
    trail_atr_mult=2.5,
    exit_window=BARS_PER_DAY // 2,
)


_EH06R_BASE = EdgeParams(
    family="ratio_divergence_v2",
    div_window=30 * BARS_PER_DAY,
    div_thr=1.0,
    ratio_source="sum",
    div_mode="follow_top",
    gate_mode="trigger",
    gate_break_window=48,
    stop_atr_mult=1.5,
    tp_atr_mult=2.0,
    trail_atr_mult=None,
    use_structure_exit=False,
    exit_window=BARS_PER_DAY // 2,
)

_EH09R_BASE = EdgeParams(
    family="taker_absorb_v2",
    taker_window=16,
    taker_slope_thr=0.0,
    taker_mode="absorb",
    taker_source="metrics",
    stop_atr_mult=1.5,
    tp_atr_mult=2.0,
    trail_atr_mult=None,
    use_structure_exit=False,
    exit_window=BARS_PER_DAY // 2,
)


def _pack(
    prefix: str,
    hyp: str,
    base: EdgeParams,
    items: list[tuple[str, str, str, dict[str, Any]]],
) -> dict[str, tuple[EdgeParams, str, str, str, str]]:
    out: dict[str, tuple[EdgeParams, str, str, str, str]] = {}
    for suffix, knob, why, over in items:
        lid = f"{prefix}_{suffix}"
        out[lid] = (replace(base, **over), hyp, f"{hyp} {knob}", knob, why)
    return out


CYCLE_EDGE_R: dict[str, tuple[EdgeParams, str, str, str, str]] = {}

# --- Phase 1: EH-01R — exit and position construction (entry condition frozen)
CYCLE_EDGE_R.update(
    _pack(
        "eh01r",
        "EH-01R",
        _EH01R_BASE,
        [
            ("base", "再掲: 突破即入り/トレール2.5", "改良前の基準線。eh01_base と同一条件。", {}),
            ("trail_off", "トレールなし（構造退出のみ）", "トレールが大勝ちを切っていないか。", {"trail_atr_mult": None}),
            ("trail_1p5", "トレール1.5ATR", "早く利確する側。", {"trail_atr_mult": 1.5}),
            ("trail_4", "トレール4ATR", "伸ばす側。", {"trail_atr_mult": 4.0}),
            ("trail_6", "トレール6ATR", "さらに伸ばす。", {"trail_atr_mult": 6.0}),
            ("stop_1p0", "損切1.0ATR", "浅い損切（枚数増）。", {"stop_atr_mult": 1.0}),
            ("stop_2p5", "損切2.5ATR", "深い損切（枚数減）。", {"stop_atr_mult": 2.5}),
            ("stop_3p5", "損切3.5ATR", "さらに深い。", {"stop_atr_mult": 3.5}),
            ("exit_24", "構造退出6h", "早い構造退出。", {"exit_window": 24}),
            ("exit_96", "構造退出24h", "遅い構造退出。", {"exit_window": BARS_PER_DAY}),
            ("exit_192", "構造退出48h", "さらに遅い。", {"exit_window": 2 * BARS_PER_DAY}),
            ("exit_off", "構造退出なし", "構造退出の寄与を見る。", {"use_structure_exit": False}),
            ("tp_3atr", "利確3ATR（トレールなし）", "固定目標との対照。", {"tp_atr_mult": 3.0, "trail_atr_mult": None}),
            ("tp_6atr", "利確6ATR（トレールなし）", "遠い固定目標。", {"tp_atr_mult": 6.0, "trail_atr_mult": None}),
            ("entry_confirm", "1本後も突破維持を確認", "だまし突破を落とす建て方。", {"entry_mode": "confirm"}),
            ("entry_delay_4", "1時間待って入る", "初動の高値掴みを避ける。", {"entry_mode": "delay", "entry_delay": 4}),
            ("entry_delay_8", "2時間待って入る", "より待つ。", {"entry_mode": "delay", "entry_delay": 8}),
            ("entry_retest", "突破水準への戻りで入る", "建値を良くする。取りこぼしと引き換え。", {"entry_mode": "retest"}),
            ("entry_retest_tight", "戻り許容0.2ATR", "より厳しい戻り。", {"entry_mode": "retest", "retest_tol_atr": 0.2}),
            ("entry_retest_24", "戻り待ち6hまで", "待ち時間を短く。", {"entry_mode": "retest", "retest_window": 24}),
            ("retest_trail_4", "戻り入り+トレール4", "良い建値と長い保有の組合せ。", {"entry_mode": "retest", "trail_atr_mult": 4.0}),
            ("retest_stop_2p5", "戻り入り+損切2.5", "良い建値と深い損切。", {"entry_mode": "retest", "stop_atr_mult": 2.5}),
            ("brk192_trail_4", "48h突破+トレール4", "両期間PASSした足長版を伸ばす。", {"break_window": 192, "trail_atr_mult": 4.0}),
            ("brk192_retest", "48h突破+戻り入り", "足長版の建値改善。", {"break_window": 192, "entry_mode": "retest"}),
        ],
    )
)

# --- Phase 2: EH-07R — rebuild the entry trigger
CYCLE_EDGE_R.update(
    _pack(
        "eh07r",
        "EH-07R",
        _EH07R_BASE,
        [
            ("base", "再掲: 2本遅延で入る", "改良前の基準線。eh07_base と同一条件。", {"flush_trigger": "delay", "flush_delay": 2}),
            ("stabilize", "値動きが落ち着いてから", "値幅がATRを下回った最初の足。", {"flush_trigger": "stabilize"}),
            ("stabilize_w96", "落ち着き待ち24hまで", "待ち時間を伸ばす。", {"flush_trigger": "stabilize", "trigger_window": BARS_PER_DAY}),
            ("reclaim", "ショック前の水準を取り戻したら", "洗浄が終わった証拠を価格で取る。", {"flush_trigger": "reclaim"}),
            ("reclaim_w96", "取り戻し24hまで", "待ち時間を伸ばす。", {"flush_trigger": "reclaim", "trigger_window": BARS_PER_DAY}),
            ("oi_rebuild", "建玉が積み直され始めたら", "新規が入り直した瞬間を取る。", {"flush_trigger": "oi_rebuild"}),
            ("oi_rebuild_1p0", "積み直し1.0%", "より明確な積み直し。", {"flush_trigger": "oi_rebuild", "oi_rebuild_thr": 0.01}),
            ("oi_rebuild_w96", "積み直し24hまで", "待ち時間を伸ばす。", {"flush_trigger": "oi_rebuild", "trigger_window": BARS_PER_DAY}),
            ("reclaim_stop_2p5", "取り戻し+損切2.5", "戻り待ちは損切が浅すぎる可能性。", {"flush_trigger": "reclaim", "stop_atr_mult": 2.5}),
            ("reclaim_trail", "取り戻し+トレール2.5", "目標ではなく伸ばす。", {"flush_trigger": "reclaim", "tp_atr_mult": None, "trail_atr_mult": 2.5}),
            ("oi_rebuild_trail", "積み直し+トレール2.5", "同上。", {"flush_trigger": "oi_rebuild", "tp_atr_mult": None, "trail_atr_mult": 2.5}),
            ("stabilize_trail", "落ち着き+トレール2.5", "同上。", {"flush_trigger": "stabilize", "tp_atr_mult": None, "trail_atr_mult": 2.5}),
            ("reclaim_thr0p5", "OI急減0.5%で取り戻し", "イベントを増やす。", {"flush_trigger": "reclaim", "flush_thr": 0.005}),
            ("oi_rebuild_thr0p5", "OI急減0.5%で積み直し", "イベントを増やす。", {"flush_trigger": "oi_rebuild", "flush_thr": 0.005}),
            ("reclaim_range1p5", "値幅1.5ATRで取り戻し", "イベントを増やす。", {"flush_trigger": "reclaim", "flush_range_mult": 1.5}),
            ("reclaim_pre48", "元方向48h+取り戻し", "方向判定を長くする。", {"flush_trigger": "reclaim", "pre_trend_window": 2 * BARS_PER_DAY}),
            ("oi_rebuild_pre48", "元方向48h+積み直し", "同上。", {"flush_trigger": "oi_rebuild", "pre_trend_window": 2 * BARS_PER_DAY}),
            ("reclaim_tp3", "取り戻し+利確3ATR", "目標を伸ばす。", {"flush_trigger": "reclaim", "tp_atr_mult": 3.0}),
            # 清算イベント自体が希少で n<100 が構造的。小さな洗浄まで拾う版を用意する。
            (
                "hifreq_reclaim",
                "小さな洗浄まで拾う+取り戻し",
                "OI急減0.3%・値幅1.2ATR。回数がゲートに届くかを見る。",
                {"flush_trigger": "reclaim", "flush_thr": 0.003, "flush_range_mult": 1.2},
            ),
            (
                "hifreq_rebuild",
                "小さな洗浄まで拾う+積み直し",
                "同上を積み直しトリガで。",
                {"flush_trigger": "oi_rebuild", "flush_thr": 0.003, "flush_range_mult": 1.2},
            ),
            (
                "hifreq_delay",
                "小さな洗浄まで拾う+2本遅延",
                "同上を旧トリガで（対照）。",
                {"flush_trigger": "delay", "flush_delay": 2, "flush_thr": 0.003, "flush_range_mult": 1.2},
            ),
        ],
    )
)

# --- Phase 3: EH-02R — re-measure the lead, use it as a gate
CYCLE_EDGE_R.update(
    _pack(
        "eh02r",
        "EH-02R",
        _EH02R_BASE,
        [
            ("base", "12h突破 × 現物先行z>0.5", "本命。乖離を絶対値でなくzで測り、頻度のある引き金に載せる。", {}),
            ("ctrl_no_gate", "対照: ゲートなし", "同じ突破を無条件で。差が出るかが全て。", {"lead_mode": "any"}),
            ("ctrl_perp_gate", "対照: 先物先行ゲート", "符号反転。逆の結果が出るか。", {"lead_mode": "perp"}),
            ("z_1p0", "z>1.0", "より強い先行のみ。", {"lead_z_thr": 1.0}),
            ("z_1p5", "z>1.5", "さらに厳しく。", {"lead_z_thr": 1.5}),
            ("z_0p25", "z>0.25", "回数寄り。", {"lead_z_thr": 0.25}),
            ("cum", "累積乖離で測る", "1本ごとの差を積み上げる測り方。", {"lead_measure": "cum"}),
            ("cum_16", "累積乖離4h", "長い累積。", {"lead_measure": "cum", "lead_window": 16}),
            ("spread", "価格差の変化で測る", "リターン差でなく現物先物スプレッドの変化。", {"lead_measure": "spread"}),
            ("spread_16", "価格差の変化4h", "長い窓。", {"lead_measure": "spread", "lead_window": 16}),
            ("win_16", "先行計測4h", "リターン差の窓を伸ばす。", {"lead_window": 16}),
            ("win_2", "先行計測30分", "短い窓。", {"lead_window": 2}),
            ("zwin_10d", "z基準10日", "短い基準期間。", {"lead_z_window": 10 * BARS_PER_DAY}),
            ("brk_96", "24h突破に載せる", "引き金を長くする。", {"gate_break_window": BARS_PER_DAY}),
            ("brk_16", "4h突破に載せる", "引き金を短くする（回数増）。", {"gate_break_window": 16}),
            ("trigger_only", "ゲートでなく単独の引き金", "旧EH-02の形をzで測り直したもの。", {"gate_mode": "trigger"}),
            ("trail_4", "トレール4ATR", "伸ばす。", {"trail_atr_mult": 4.0}),
            ("long_only", "ロングのみ", "方向の切り分け。", {"long_only": True}),
        ],
    )
)


# --- Phase 4: EH-06R — cut turnover and drawdown
# The 100-cycle base traded 809 (B) / 1187 (C) times with DD 31.6% / 51.0%.
# The divergence itself replicated; the way it was traded did not survive.
CYCLE_EDGE_R.update(
    _pack(
        "eh06r",
        "EH-06R",
        _EH06R_BASE,
        [
            ("base", "再掲: 乖離1.0σで即入り", "改良前の基準線。eh06_base と同一条件。", {}),
            ("ctrl_follow_retail", "対照: 個人側に付く", "符号反転の対照を新しい退出で再掲。", {"div_mode": "follow_retail"}),
            ("cool_96", "24hクールダウン", "同じ乖離で何度も撃たない。回転とDDの主因。", {"cooldown_bars": BARS_PER_DAY}),
            ("cool_192", "48hクールダウン", "さらに絞る。", {"cooldown_bars": 2 * BARS_PER_DAY}),
            ("cool_32", "8hクールダウン", "軽く絞る。", {"cooldown_bars": 32}),
            ("persist_8", "乖離が2h続いてから", "一瞬の乖離を捨てる。", {"persist_bars": 8}),
            ("persist_32", "乖離が8h続いてから", "より強い持続。", {"persist_bars": 32}),
            ("both_extreme", "個人・上位の両方が偏っている", "差だけでなく各side自体の偏りを要求。", {"both_extreme": True}),
            ("thr_2p0", "乖離2.0σ", "より極端のみ。", {"div_thr": 2.0}),
            ("gate_break", "12h突破のゲートとして使う", "逆張りでなく順張りの条件にする。", {"gate_mode": "gate"}),
            ("gate_break_ctrl", "対照: ゲートなしの突破", "ゲートの寄与を測る対照。", {"gate_mode": "gate", "div_thr": -99.0}),
            ("gate_break_96", "24h突破のゲート", "引き金を長くする。", {"gate_mode": "gate", "gate_break_window": BARS_PER_DAY}),
            ("struct_exit", "構造退出のみ（目標なし）", "前フェーズの学び: 目標/トレールで勝ちを切らない。", {"tp_atr_mult": None, "use_structure_exit": True}),
            ("trail_4", "トレール4ATR", "同上。緩いトレール。", {"tp_atr_mult": None, "trail_atr_mult": 4.0}),
            ("tp_4atr", "利確4ATR", "目標を遠くする。", {"tp_atr_mult": 4.0}),
            ("stop_2p5", "損切2.5ATR", "浅い損切がDDを増やしていないか。", {"stop_atr_mult": 2.5}),
            ("win_10d", "基準窓10日", "100サイクルで唯一PASSした窓を新しい枠で。", {"div_window": 10 * BARS_PER_DAY}),
            ("count_ratio", "上位比=口座数版", "比率の取り方。", {"ratio_source": "count"}),
            ("cool96_struct", "24hクールダウン+構造退出", "回転を絞って伸ばす組合せ。", {"cooldown_bars": BARS_PER_DAY, "tp_atr_mult": None, "use_structure_exit": True}),
            ("cool96_thr2", "24hクールダウン+乖離2.0σ", "絞りを二重にする。", {"cooldown_bars": BARS_PER_DAY, "div_thr": 2.0}),
        ],
    )
)

# --- Phase 5: EH-09R — re-measure the aggressive flow, then fix the exit
CYCLE_EDGE_R.update(
    _pack(
        "eh09r",
        "EH-09R",
        _EH09R_BASE,
        [
            ("base", "再掲: metrics成行比の傾き", "改良前の基準線。eh09_base と同一条件。", {}),
            ("ctrl_confirm", "対照: 成行と同方向（順張り）", "符号反転の対照を再掲。", {"taker_mode": "confirm"}),
            ("perp_vol", "先物出来高から成行比を作る", "metricsの集計値でなく約定出来高で測り直す。", {"taker_source": "perp_vol"}),
            ("perp_vol_w32", "出来高版+計測8h", "測り直し版で窓を伸ばす。", {"taker_source": "perp_vol", "taker_window": 32}),
            ("perp_vol_slope", "出来高版+傾き閾値0.05", "測り直し版に閾値。", {"taker_source": "perp_vol", "taker_slope_thr": 0.05}),
            ("perp_vol_ctrl", "対照: 出来高版で順張り", "測り直し版の符号反転。", {"taker_source": "perp_vol", "taker_mode": "confirm"}),
            ("slope_0p05", "傾き閾値0.05", "Set Bで最良だったノブを再掲。", {"taker_slope_thr": 0.05}),
            ("struct_exit", "構造退出のみ（目標なし）", "前フェーズの学び。", {"tp_atr_mult": None, "use_structure_exit": True}),
            ("trail_4", "トレール4ATR", "同上。", {"tp_atr_mult": None, "trail_atr_mult": 4.0}),
            ("tp_4atr", "利確4ATR", "目標を遠くする。", {"tp_atr_mult": 4.0}),
            ("stop_2p5", "損切2.5ATR", "踏まれ耐性。", {"stop_atr_mult": 2.5}),
            ("extend_0p5", "高値を0.5ATR超えてから", "わずかな更新を捨てる。", {"extend_atr": 0.5}),
            ("extend_1p0", "高値を1.0ATR超えてから", "より明確な更新のみ。", {"extend_atr": 1.0}),
            ("cool_96", "24hクールダウン", "回転を落とす。", {"cooldown_bars": BARS_PER_DAY}),
            ("cool_32", "8hクールダウン", "軽く落とす。", {"cooldown_bars": 32}),
            ("persist_8", "減衰が2h続いてから", "一瞬の減衰を捨てる。", {"persist_bars": 8}),
            ("short_only", "ショートのみ", "高値側だけ。", {"short_only": True}),
            ("slope05_struct", "傾き0.05+構造退出", "最良ノブと新しい退出の組合せ。", {"taker_slope_thr": 0.05, "tp_atr_mult": None, "use_structure_exit": True}),
            ("perpvol_struct", "出来高版+構造退出", "測り直しと新しい退出の組合せ。", {"taker_source": "perp_vol", "tp_atr_mult": None, "use_structure_exit": True}),
            ("slope05_cool96", "傾き0.05+24hクールダウン", "最良ノブに回転制限。", {"taker_slope_thr": 0.05, "cooldown_bars": BARS_PER_DAY}),
        ],
    )
)


def prepare_cycle_edge_r(logic_id: str, m15: pd.DataFrame, deriv: pd.DataFrame) -> pd.DataFrame:
    params, *_ = CYCLE_EDGE_R[logic_id]
    return edge.prepare_frames(m15, deriv, params)
