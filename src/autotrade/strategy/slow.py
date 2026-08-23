"""SH-01 — daily-scale trend continuation, sized so that cost stops mattering.

The measurement that motivates this module is in
``eval/reports/20260823-cost-horizon.md``: with a 1h ATR stop the round-trip
cost eats 14-19% of the risk budget on every trade, which is why 217 previous
evaluations hovered around zero. On a daily ATR the same cost is 2.5-3.2%.

So the stop distance, not the signal, is the primary design variable here.
Everything else follows the defaults the earlier phases established:

- no fixed take profit, because fixed targets cut the winners that pay for
  the losers (v1 postmortem)
- no tight trailing stop, for the same reason (EH-01R)
- no waiting after the trigger, because delay and retest both lost (EH-01R)

Signals are evaluated on 4h bars and executed on the 15m grid, so intrabar
stop/target resolution stays fine-grained while the strategy itself is slow.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import pandas as pd

from autotrade.indicators import atr
from autotrade.strategy.common import norm_ohlcv

BARS_PER_DAY = 96
BARS_PER_4H = 16


@dataclass
class SlowParams:
    # --- entry
    entry_days: int = 20
    entry_tf: str = "4h"  # bar close used to confirm the break
    # --- exit
    exit_days: int = 10
    # --- risk
    atr_tf: str = "1d"  # 1d | 4h
    atr_period: int = 14
    stop_atr_mult: float = 1.5
    tp_atr_mult: float | None = None
    trail_atr_mult: float | None = None
    min_stop_pct: float = 0.5
    # --- regime
    regime_days: int = 0  # 0 = off; else trade only with the N-day SMA
    regime_mode: str = "with"  # with | against
    # --- EH-06 divergence veto (needs derivative columns)
    veto_mode: str = "off"  # off | block_against | block_with
    veto_window_days: int = 30
    veto_thr: float = 1.0
    # --- direction
    long_only: bool = False
    short_only: bool = False
    # --- falsification: a slow edge should survive being acted on late
    signal_delay_bars: int = 0


def _tf_atr(m15: pd.DataFrame, tf: str, period: int) -> pd.Series:
    """ATR on a slower bar, mapped back to 15m with a full-bar lag.

    The lag matters: without it the 15m bars inside an unfinished daily bar
    would see that bar's own range.
    """
    rule = {"1d": "1D", "4h": "4h", "1h": "1h"}[tf]
    slow = m15.resample(rule, label="left", closed="left").agg(
        {"high": "max", "low": "min", "close": "last"}
    )
    a = atr(slow["high"], slow["low"], slow["close"], period)
    a.index = a.index + pd.tseries.frequencies.to_offset(rule)
    return a.reindex(m15.index, method="ffill")


def _tf_close(m15: pd.DataFrame, tf: str) -> pd.Series:
    """Last close of the most recently *finished* bar on a slower timeframe."""
    rule = {"1d": "1D", "4h": "4h", "1h": "1h"}[tf]
    slow = m15["close"].resample(rule, label="left", closed="left").last()
    slow.index = slow.index + pd.tseries.frequencies.to_offset(rule)
    return slow.reindex(m15.index, method="ffill")


def _bar_boundary(m15: pd.DataFrame, tf: str) -> pd.Series:
    """True on the first 15m bar after a slower bar closes."""
    rule = {"1d": "1D", "4h": "4h", "1h": "1h"}[tf]
    stamp = m15.index.floor(rule)
    return pd.Series(stamp != pd.Series(stamp, index=m15.index).shift(1), index=m15.index)


def _daily_channel(m15: pd.DataFrame, days: int, kind: str, lag_days: int = 0) -> pd.Series:
    """Highest high / lowest low of the last ``days`` *completed* daily bars.

    Building the channel from 15m highs instead would fold the current day's
    own range into it, and a close can essentially never exceed a channel that
    contains it -- the first version of this file produced zero signals for
    exactly that reason.
    """
    daily = m15.resample("1D", label="left", closed="left").agg({"high": "max", "low": "min"})
    col = daily["high"] if kind == "high" else daily["low"]
    roll = (
        col.rolling(days, min_periods=days).max()
        if kind == "high"
        else col.rolling(days, min_periods=days).min()
    )
    # Value labelled at day d covers days d-days+1..d, so it is only usable
    # from day d+1 onwards. ``lag_days`` pushes it further out when the closing
    # bar being compared against it is itself a daily bar.
    roll.index = roll.index + pd.Timedelta(days=1 + lag_days)
    return roll.reindex(m15.index, method="ffill")


def _first_true(cond: pd.Series) -> pd.Series:
    c = cond.fillna(False).astype(bool)
    return c & ~c.shift(1).fillna(False)


def _sma(m15: pd.DataFrame, days: int) -> pd.Series:
    daily = m15["close"].resample("1D", label="left", closed="left").last()
    s = daily.rolling(days, min_periods=days).mean()
    s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(m15.index, method="ffill")


def _zscore(s: pd.Series, window: int) -> pd.Series:
    m = s.rolling(window, min_periods=max(window // 4, 20)).mean()
    sd = s.rolling(window, min_periods=max(window // 4, 20)).std()
    return (s - m) / sd.replace(0.0, float("nan"))


def _divergence(f: pd.DataFrame, p: SlowParams) -> pd.Series:
    """Retail minus top-trader positioning, in standard deviations.

    Positive means the crowd is longer than the large accounts. EH-06 showed
    across three periods that taking the crowd's side loses reliably, so this
    is used only to refuse trades, never to open them.
    """
    win = p.veto_window_days * BARS_PER_DAY
    return _zscore(f["acct_ratio"], win) - _zscore(f["tt_ratio"], win)


def prepare_frames(
    m15: pd.DataFrame,
    params: SlowParams,
    deriv: pd.DataFrame | None = None,
) -> pd.DataFrame:
    f = norm_ohlcv(m15)
    if deriv is not None:
        ctx = deriv.reindex(f.index)
        for col in ctx.columns:
            f[col] = ctx[col]

    # A daily confirming close sits inside the current day's channel value, so
    # the channel has to step back one more day for it to be a real break.
    entry_lag = 1 if params.entry_tf == "1d" else 0
    hi = _daily_channel(f, params.entry_days, "high", entry_lag)
    lo = _daily_channel(f, params.entry_days, "low", entry_lag)

    # Confirm on the slower bar's close rather than any 15m tick through the
    # level: this is the "no intrabar breakout chasing" rule.
    close_tf = _tf_close(f, params.entry_tf)
    boundary = _bar_boundary(f, params.entry_tf)
    long_c = _first_true(close_tf > hi) & boundary
    short_c = _first_true(close_tf < lo) & boundary

    if params.regime_days:
        sma = _sma(f, params.regime_days)
        up, down = f["close"] > sma, f["close"] < sma
        if params.regime_mode == "with":
            long_c, short_c = long_c & up, short_c & down
        else:
            long_c, short_c = long_c & down, short_c & up

    if params.veto_mode != "off":
        div = _divergence(f, params)
        crowd_long = div > params.veto_thr
        crowd_short = div < -params.veto_thr
        if params.veto_mode == "block_against":
            # Refuse to stand on the crowd's side of the trade.
            long_c, short_c = long_c & ~crowd_long, short_c & ~crowd_short
        else:
            # Inverted control: refuse the trades the veto would have kept.
            long_c, short_c = long_c & ~crowd_short, short_c & ~crowd_long

    if params.signal_delay_bars:
        long_c = long_c.shift(params.signal_delay_bars).fillna(False)
        short_c = short_c.shift(params.signal_delay_bars).fillna(False)

    if params.long_only:
        short_c = pd.Series(False, index=f.index)
    if params.short_only:
        long_c = pd.Series(False, index=f.index)

    f["long_signal"] = long_c.fillna(False).astype(bool)
    f["short_signal"] = short_c.fillna(False).astype(bool)

    a = _tf_atr(f, params.atr_tf, params.atr_period)
    f["atr"] = a
    f["stop_pct"] = (a / f["close"] * 100.0 * params.stop_atr_mult).clip(
        lower=params.min_stop_pct
    ).fillna(params.min_stop_pct)
    if params.tp_atr_mult is None:
        f["tp_pct"] = float("nan")
    else:
        f["tp_pct"] = (a / f["close"] * 100.0 * params.tp_atr_mult).fillna(
            params.min_stop_pct * 2
        )
    f["trail_atr_mult"] = (
        float("nan") if params.trail_atr_mult is None else float(params.trail_atr_mult)
    )

    exit_lo = _daily_channel(f, params.exit_days, "low")
    exit_hi = _daily_channel(f, params.exit_days, "high")
    f["structure_exit_long"] = (f["close"] < exit_lo).fillna(False)
    f["structure_exit_short"] = (f["close"] > exit_hi).fillna(False)

    f["h4_long_break"] = False
    f["h4_short_break"] = False
    f["daily_against_long"] = False
    f["daily_against_short"] = False
    return f


# --------------------------------------------------------------------------- pack

_BASE = SlowParams()

_VARIANTS: list[tuple[str, str, str, dict[str, Any]]] = [
    ("base", "基準: 20日高値を4h終値で抜けたら / 10日安値で退出 / 損切1.5日足ATR",
     "コストがRの2.5〜3.2%に収まる最小構成。ここが出発点。", {}),
    ("entry_10d", "入口10日", "引き金の長さ。短いほど回数は増える。", {"entry_days": 10}),
    ("entry_40d", "入口40日", "引き金の長さ。", {"entry_days": 40}),
    ("entry_55d", "入口55日", "引き金の長さ。", {"entry_days": 55}),
    ("exit_5d", "退出5日", "利を伸ばす距離。短い＝早く降りる。", {"exit_days": 5}),
    ("exit_20d", "退出20日", "利を伸ばす距離。", {"exit_days": 20}),
    ("stop_1atr", "損切1.0日足ATR", "リスク距離。cost/R は約4.7%まで上がる。", {"stop_atr_mult": 1.0}),
    ("stop_2p5atr", "損切2.5日足ATR", "リスク距離。cost/R は約1.9%。", {"stop_atr_mult": 2.5}),
    ("atr_4h", "ATRを4h足で測る", "コスト比の検証。cost/R が 6.4% に上がるはず。", {"atr_tf": "4h"}),
    ("entry_1d", "入口判定を日足終値に", "引き金の粒度。", {"entry_tf": "1d"}),
    ("trail_4", "トレール4ATR併用", "構造退出に加えてトレール。4未満は勝ちを切ると判明済み。",
     {"trail_atr_mult": 4.0}),
    ("tp_4atr", "利確4ATR", "固定利確は過去に負けている。対照として再確認する。",
     {"tp_atr_mult": 4.0}),
    ("regime_200d", "200日線と同じ向きだけ", "地合いフィルタ。", {"regime_days": 200}),
    ("regime_100d", "100日線と同じ向きだけ", "地合いフィルタ。", {"regime_days": 100}),
    ("regime_against", "対照: 200日線と逆向きだけ", "地合いフィルタの符号反転。",
     {"regime_days": 200, "regime_mode": "against"}),
    ("long_only", "ロングのみ", "方向の偏り。", {"long_only": True}),
    ("short_only", "ショートのみ", "方向の偏り。", {"short_only": True}),
    ("veto_1p0", "EH-06拒否フィルタ（1.0σ）", "群衆と同じ側に立つ取引を拒否する。",
     {"veto_mode": "block_against", "veto_thr": 1.0}),
    ("veto_0p5", "EH-06拒否フィルタ（0.5σ）", "拒否の強さ。", {"veto_mode": "block_against", "veto_thr": 0.5}),
    ("veto_2p0", "EH-06拒否フィルタ（2.0σ）", "拒否の強さ。", {"veto_mode": "block_against", "veto_thr": 2.0}),
    ("veto_0", "EH-06拒否フィルタ（符号のみ）",
     "閾値を0にして半分に割る。1.0σではほとんど発火しないため、効きを測れる形にする。",
     {"veto_mode": "block_against", "veto_thr": 0.0}),
    ("veto_0_ctrl", "対照: 符号のみで向きを反転", "上の符号反転。",
     {"veto_mode": "block_with", "veto_thr": 0.0}),
    ("veto_ctrl", "対照: 拒否の向きを反転", "拒否フィルタの符号反転。差を読むための対照。",
     {"veto_mode": "block_with", "veto_thr": 1.0}),
    ("delay_1h", "反証: シグナルを1時間遅らせる",
     "遅らせても残るなら先読みではない。日足規模のエッジが1時間で消えるはずがない。",
     {"signal_delay_bars": 4}),
    ("delay_1d", "反証: シグナルを1日遅らせる",
     "同上。ここまで遅らせて残るかは、エッジの持続時間そのものの測定でもある。",
     {"signal_delay_bars": BARS_PER_DAY}),
    ("tp4_delay_1h", "反証: 3期間PASS版を1時間遅らせる",
     "唯一3期間ゲートを通った設定を、同じやり方で疑う。",
     {"tp_atr_mult": 4.0, "signal_delay_bars": 4}),
    ("tp4_delay_1d", "反証: 3期間PASS版を1日遅らせる", "同上。",
     {"tp_atr_mult": 4.0, "signal_delay_bars": BARS_PER_DAY}),
]

CYCLE_SLOW: dict[str, tuple[SlowParams, str, str, str, str]] = {
    f"sh01_{name}": (replace(_BASE, **over), "SH-01", f"SH-01 {knob}", knob, why)
    for name, knob, why, over in _VARIANTS
}

NEEDS_DERIVATIVES = {lid for lid, (p, *_) in CYCLE_SLOW.items() if p.veto_mode != "off"}


def prepare_slow(
    logic_id: str, m15: pd.DataFrame, deriv: pd.DataFrame | None = None
) -> pd.DataFrame:
    params = CYCLE_SLOW[logic_id][0]
    return prepare_frames(m15, params, deriv if params.veto_mode != "off" else None)
