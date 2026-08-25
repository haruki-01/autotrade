"""固定ブラケット枠（1:2・保有上限6時間）で15分足のエントリー条件を試す。

枠は `scripts/calibrate_bracket.py` の実測で確定している。

    損切り 0.35% ／ 利確 0.70% ／ 保有上限 6時間 → 6時間以内決済率 89.9%

この枠の良いところは**判定基準が理論から出る**こと。ドリフトのない価格に
対して 1:2 ブラケットの当たり率は 1/3 に決まるので、勝率が33%台なら
そのシグナルには情報が無いと即断できる。ここでは各条件の勝率が 1/3 から
どれだけ上振れるかだけを見る。

値幅・保有上限・RR はすべて固定なので、条件ごとに変わるのは
**いつ入るか**と**どちら向きか**だけ。one-point change が自然に守られる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

# 現行枠（2026-08-25）: 保有12時間 / 損切り1.00% / RR 1:1.5 / 同時1枠。
# 入口は1分足。15分足で測った「同じ時間の窓」になるよう、バー数は×15する。
#
# 必要上振れ = (往復コスト率 / 損切り幅) / (1 + RR)
# 12時間で決済率70%を満たす最大幅が 1.00%（必要 +2.9pt）。
# 旧6時間枠は 0.70%（必要 +4.2pt）。
STOP_PCT = 0.010
RR = 1.5
MAX_HOURS = 12.0
BARS_PER_HOUR = 4  # 15分足。1分足は BARS_PER_HOUR_1M
BARS_PER_HOUR_1M = 60
M15_TO_1M = 15


def scan_bracket(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    entries: np.ndarray,
    *,
    direction: int,
    stop_pct: float,
    rr: float,
    max_bars: int,
) -> dict[str, float]:
    """与えたエントリー点について、損切り/利確のどちらが先に触るかを前進走査する。

    同じ足で両方に触った場合は**損切り優先**。足の中の順序は15分足からは
    分からないので悲観側に寄せる。値幅の実測と総当たりで共用する。
    """
    n = len(close)
    wins = losses = timeouts = 0
    bars: list[int] = []
    timeout_r: list[float] = []

    for i in entries:
        entry = close[i]
        if direction > 0:
            stop_px, tp_px = entry * (1 - stop_pct), entry * (1 + stop_pct * rr)
        else:
            stop_px, tp_px = entry * (1 + stop_pct), entry * (1 - stop_pct * rr)

        end = min(i + max_bars, n - 1)
        hit = None
        for j in range(i + 1, end + 1):
            if direction > 0:
                hit_stop = low[j] <= stop_px
                hit_tp = high[j] >= tp_px
            else:
                hit_stop = high[j] >= stop_px
                hit_tp = low[j] <= tp_px
            if hit_stop:
                hit = ("loss", j)
                break
            if hit_tp:
                hit = ("win", j)
                break

        if hit is None:
            timeouts += 1
            bars.append(end - i)
            timeout_r.append((close[end] - entry) / entry * direction / stop_pct)
        else:
            kind, j = hit
            bars.append(j - i)
            if kind == "win":
                wins += 1
            else:
                losses += 1

    total = wins + losses + timeouts
    if total == 0:
        return {}
    resolved = wins + losses
    ev_r = (wins * rr - losses + float(np.sum(timeout_r))) / total
    return {
        "n": float(total),
        "resolve_rate": resolved / total,
        "win_rate_resolved": wins / resolved if resolved else float("nan"),
        "timeout_rate": timeouts / total,
        "ev_r": ev_r,
        "mean_bars": float(np.mean(bars)) if bars else float("nan"),
        "median_bars": float(np.median(bars)) if bars else float("nan"),
    }


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    pc = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


@dataclass
class Signals:
    """各足で +1（ロング）/ -1（ショート）/ 0（何もしない）。"""

    values: np.ndarray


SignalFn = Callable[[pd.DataFrame, dict], Signals]


def sig_random(df: pd.DataFrame, p: dict) -> Signals:
    """対照。情報ゼロの基準線を同じ計測系の中で作る。

    理論値 1/3 と一致するはずで、しなければ計測側にバグがある。
    """
    rng = np.random.default_rng(int(p.get("seed", 11)))
    rate = float(p.get("rate", 0.02))
    draw = rng.random(len(df))
    side = np.where(rng.random(len(df)) < 0.5, 1, -1)
    return Signals(np.where(draw < rate, side, 0).astype(np.int8))


def sig_ema_cross(df: pd.DataFrame, p: dict) -> Signals:
    fast, slow = int(p.get("fast", 12)), int(p.get("slow", 48))
    f, s = _ema(df["close"], fast), _ema(df["close"], slow)
    up = (f > s) & (f.shift(1) <= s.shift(1))
    dn = (f < s) & (f.shift(1) >= s.shift(1))
    return Signals(np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8))


def sig_donchian(df: pd.DataFrame, p: dict) -> Signals:
    n = int(p.get("window", 24))
    hh = df["high"].rolling(n).max().shift(1)
    ll = df["low"].rolling(n).min().shift(1)
    up = df["close"] > hh
    dn = df["close"] < ll
    return Signals(np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8))


def sig_donchian_fade(df: pd.DataFrame, p: dict) -> Signals:
    """ブレイクの逆張り。継続と反転のどちらに歪みがあるかを分ける。"""
    n = int(p.get("window", 24))
    hh = df["high"].rolling(n).max().shift(1)
    ll = df["low"].rolling(n).min().shift(1)
    up = df["close"] > hh
    dn = df["close"] < ll
    return Signals(np.where(up, -1, np.where(dn, 1, 0)).astype(np.int8))


def sig_rsi_revert(df: pd.DataFrame, p: dict) -> Signals:
    n, lo, hi = int(p.get("n", 14)), float(p.get("lo", 30)), float(p.get("hi", 70))
    r = _rsi(df["close"], n)
    cross_lo = (r < lo) & (r.shift(1) >= lo)
    cross_hi = (r > hi) & (r.shift(1) <= hi)
    return Signals(np.where(cross_lo, 1, np.where(cross_hi, -1, 0)).astype(np.int8))


def sig_runs_resampled(df: pd.DataFrame, p: dict) -> Signals:
    """上位足で連続を数え、その足の確定1分にだけシグナルを置く。先読みしない。"""
    k = int(p.get("k", 5))
    rule = str(p.get("rule", "15min"))
    ohlc = (
        df.resample(rule, label="left", closed="left")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
    )
    s15 = sig_runs(ohlc, {"k": k}).values
    minutes = int(pd.Timedelta(rule).total_seconds() // 60)
    fire_at = ohlc.index + pd.Timedelta(minutes=minutes - 1)
    mapped = pd.Series(s15, index=fire_at)
    aligned = mapped.reindex(df.index).fillna(0).astype(np.int8)
    return Signals(aligned.to_numpy())


def sig_runs(df: pd.DataFrame, p: dict) -> Signals:
    """同方向の足が k 本続いたあと。継続側に賭ける。"""
    k = int(p.get("k", 4))
    up_bar = df["close"] > df["open"]
    up = up_bar.rolling(k).sum() == k
    dn = (~up_bar).rolling(k).sum() == k
    return Signals(np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8))


def sig_runs_fade(df: pd.DataFrame, p: dict) -> Signals:
    k = int(p.get("k", 4))
    up_bar = df["close"] > df["open"]
    up = up_bar.rolling(k).sum() == k
    dn = (~up_bar).rolling(k).sum() == k
    return Signals(np.where(up, -1, np.where(dn, 1, 0)).astype(np.int8))


def sig_squeeze_break(df: pd.DataFrame, p: dict) -> Signals:
    """ボラ収縮のあとのレンジ抜け。値幅が固定なので収縮期を選ぶ意味がある。"""
    n, look, q = int(p.get("n", 14)), int(p.get("look", 96)), float(p.get("q", 0.3))
    atr = _atr(df, n)
    thr = atr.rolling(look).quantile(q)
    quiet = atr <= thr
    hh = df["high"].rolling(int(p.get("window", 12))).max().shift(1)
    ll = df["low"].rolling(int(p.get("window", 12))).min().shift(1)
    up = quiet & (df["close"] > hh)
    dn = quiet & (df["close"] < ll)
    return Signals(np.where(up, 1, np.where(dn, -1, 0)).astype(np.int8))


def sig_vol_spike(df: pd.DataFrame, p: dict) -> Signals:
    mult, look = float(p.get("mult", 3.0)), int(p.get("look", 96))
    med = df["volume"].rolling(look).median()
    spike = df["volume"] > mult * med
    up_bar = df["close"] > df["open"]
    return Signals(
        np.where(spike & up_bar, 1, np.where(spike & ~up_bar, -1, 0)).astype(np.int8)
    )


def sig_vol_spike_fade(df: pd.DataFrame, p: dict) -> Signals:
    mult, look = float(p.get("mult", 3.0)), int(p.get("look", 96))
    med = df["volume"].rolling(look).median()
    spike = df["volume"] > mult * med
    up_bar = df["close"] > df["open"]
    return Signals(
        np.where(spike & up_bar, -1, np.where(spike & ~up_bar, 1, 0)).astype(np.int8)
    )


def sig_trend_pullback(df: pd.DataFrame, p: dict) -> Signals:
    """上位足の向きに沿って、短期の押し目/戻りで入る。"""
    slow, fast = int(p.get("slow", 192)), int(p.get("fast", 12))
    lo, hi = float(p.get("lo", 40)), float(p.get("hi", 60))
    trend = _ema(df["close"], slow)
    up_trend = df["close"] > trend
    r = _rsi(df["close"], int(p.get("rsi", 14)))
    pull_lo = (r < lo) & (r.shift(1) >= lo)
    pull_hi = (r > hi) & (r.shift(1) <= hi)
    del fast
    return Signals(
        np.where(up_trend & pull_lo, 1, np.where(~up_trend & pull_hi, -1, 0)).astype(np.int8)
    )


def sig_session(df: pd.DataFrame, p: dict) -> Signals:
    """特定時間帯の最初の足。流動性の時間帯構造に歪みがあるかを見る。"""
    hour = int(p.get("hour", 13))  # UTC 13時 = 米国株の寄り前後
    side = int(p.get("side", 1))
    h = df.index.hour
    m = df.index.minute
    fire = (h == hour) & (m == 0)
    return Signals(np.where(fire, side, 0).astype(np.int8))


def sig_gap_revert(df: pd.DataFrame, p: dict) -> Signals:
    """直近 k 本のリターンが大きく振れた直後の逆張り。"""
    k, thr = int(p.get("k", 8)), float(p.get("thr", 0.008))
    ret = df["close"].pct_change(k)
    return Signals(
        np.where(ret < -thr, 1, np.where(ret > thr, -1, 0)).astype(np.int8)
    )


def sig_gap_follow(df: pd.DataFrame, p: dict) -> Signals:
    k, thr = int(p.get("k", 8)), float(p.get("thr", 0.008))
    ret = df["close"].pct_change(k)
    return Signals(
        np.where(ret > thr, 1, np.where(ret < -thr, -1, 0)).astype(np.int8)
    )


def _col(df: pd.DataFrame, name: str) -> pd.Series | None:
    return df[name] if name in df.columns else None


def sig_funding_side(df: pd.DataFrame, p: dict) -> Signals:
    """funding が安い方向に乗る / 高い方向を逆張り。"""
    fr = _col(df, "funding_rate")
    if fr is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    thr = float(p.get("thr", 0.0001))
    mode = str(p.get("mode", "cheap"))
    if mode == "cheap":
        # 負の funding = ショートが払っている = ロングが安い。安い側に乗る。
        return Signals(np.where(fr < -thr, 1, np.where(fr > thr, -1, 0)).astype(np.int8))
    # crowded: 混み合った側に乗る（cheap の対照）
    return Signals(np.where(fr > thr, 1, np.where(fr < -thr, -1, 0)).astype(np.int8))


def sig_oi_follow(df: pd.DataFrame, p: dict) -> Signals:
    """OI が増えている方向に乗る。価格が上がりつつ OI 増 = ロング積み。"""
    oi = _col(df, "oi")
    if oi is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    n = int(p.get("n", 16))
    thr = float(p.get("thr", 0.005))
    chg = oi.pct_change(n, fill_method=None)
    up = df["close"] > df["close"].shift(n)
    build = chg > thr
    return Signals(np.where(build & up, 1, np.where(build & ~up, -1, 0)).astype(np.int8))


def sig_oi_fade(df: pd.DataFrame, p: dict) -> Signals:
    """OI 急増の逆張り。混み合いの解消を狙う。"""
    oi = _col(df, "oi")
    if oi is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    n = int(p.get("n", 16))
    thr = float(p.get("thr", 0.01))
    chg = oi.pct_change(n, fill_method=None)
    up = df["close"] > df["close"].shift(n)
    crowded = chg > thr
    return Signals(np.where(crowded & up, -1, np.where(crowded & ~up, 1, 0)).astype(np.int8))


def sig_taker_follow(df: pd.DataFrame, p: dict) -> Signals:
    """taker が買い優勢ならロング。"""
    tr = _col(df, "taker_ratio")
    if tr is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    look = int(p.get("look", 96))
    q = float(p.get("q", 0.8))
    hi = tr.rolling(look).quantile(q)
    lo = tr.rolling(look).quantile(1 - q)
    return Signals(np.where(tr > hi, 1, np.where(tr < lo, -1, 0)).astype(np.int8))


def sig_taker_fade(df: pd.DataFrame, p: dict) -> Signals:
    tr = _col(df, "taker_ratio")
    if tr is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    look = int(p.get("look", 96))
    q = float(p.get("q", 0.8))
    hi = tr.rolling(look).quantile(q)
    lo = tr.rolling(look).quantile(1 - q)
    return Signals(np.where(tr > hi, -1, np.where(tr < lo, 1, 0)).astype(np.int8))


def sig_runs_funding(df: pd.DataFrame, p: dict) -> Signals:
    """連続足の継続を、funding が安い側だけに残す。br_runs_5 への one-point。"""
    base = sig_runs(df, p).values
    fr = _col(df, "funding_rate")
    if fr is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    thr = float(p.get("thr", 0.0001))
    cheap_long = fr.to_numpy() < -thr
    cheap_short = fr.to_numpy() > thr
    out = np.zeros(len(df), dtype=np.int8)
    out[(base == 1) & cheap_long] = 1
    out[(base == -1) & cheap_short] = -1
    return Signals(out)


def sig_basis_fade(df: pd.DataFrame, p: dict) -> Signals:
    """プレミアムが極端なら逆張り。"""
    prem = _col(df, "premium")
    if prem is None:
        prem = _col(df, "close_premium")
    if prem is None:
        return Signals(np.zeros(len(df), dtype=np.int8))
    look = int(p.get("look", 96 * 30))
    q = float(p.get("q", 0.9))
    hi = prem.rolling(look).quantile(q)
    lo = prem.rolling(look).quantile(1 - q)
    return Signals(np.where(prem > hi, -1, np.where(prem < lo, 1, 0)).astype(np.int8))


SIGNALS: dict[str, SignalFn] = {
    "random": sig_random,
    "ema_cross": sig_ema_cross,
    "donchian": sig_donchian,
    "donchian_fade": sig_donchian_fade,
    "rsi_revert": sig_rsi_revert,
    "runs": sig_runs,
    "runs_resampled": sig_runs_resampled,
    "runs_fade": sig_runs_fade,
    "squeeze_break": sig_squeeze_break,
    "vol_spike": sig_vol_spike,
    "vol_spike_fade": sig_vol_spike_fade,
    "trend_pullback": sig_trend_pullback,
    "session": sig_session,
    "gap_revert": sig_gap_revert,
    "gap_follow": sig_gap_follow,
    "funding_side": sig_funding_side,
    "oi_follow": sig_oi_follow,
    "oi_fade": sig_oi_fade,
    "taker_follow": sig_taker_follow,
    "taker_fade": sig_taker_fade,
    "basis_fade": sig_basis_fade,
    "runs_funding": sig_runs_funding,
}

# 1条件 = 1エントリー定義。値幅も保有上限も共通なので、比較は入口だけの差になる。
CYCLE_BRACKET: dict[str, dict] = {
    "br_random": {"signal": "random", "params": {"rate": 0.02}, "why": "対照。情報ゼロの基準線"},
    "br_random_b": {"signal": "random", "params": {"rate": 0.02, "seed": 23}, "why": "対照（別シード）"},
    "br_ema_12_48": {"signal": "ema_cross", "params": {"fast": 12, "slow": 48}, "why": "短期トレンド転換"},
    "br_ema_24_96": {"signal": "ema_cross", "params": {"fast": 24, "slow": 96}, "why": "やや長い転換"},
    "br_don_24": {"signal": "donchian", "params": {"window": 24}, "why": "6時間レンジのブレイク継続"},
    "br_don_48": {"signal": "donchian", "params": {"window": 48}, "why": "12時間レンジのブレイク継続"},
    "br_don_96": {"signal": "donchian", "params": {"window": 96}, "why": "1日レンジのブレイク継続"},
    "br_don_fade_24": {"signal": "donchian_fade", "params": {"window": 24}, "why": "ブレイクの逆張り"},
    "br_don_fade_96": {"signal": "donchian_fade", "params": {"window": 96}, "why": "日足レンジ抜けの逆張り"},
    "br_rsi_30_70": {"signal": "rsi_revert", "params": {"lo": 30, "hi": 70}, "why": "行き過ぎの反転"},
    "br_rsi_20_80": {"signal": "rsi_revert", "params": {"lo": 20, "hi": 80}, "why": "より極端な反転"},
    "br_runs_3": {"signal": "runs", "params": {"k": 3}, "why": "3連続後の継続"},
    "br_runs_5": {"signal": "runs", "params": {"k": 5}, "why": "5連続後の継続"},
    "br_runs_fade_3": {"signal": "runs_fade", "params": {"k": 3}, "why": "3連続後の反転"},
    "br_runs_fade_5": {"signal": "runs_fade", "params": {"k": 5}, "why": "5連続後の反転"},
    "br_squeeze": {"signal": "squeeze_break", "params": {"q": 0.3}, "why": "ボラ収縮後の抜け"},
    "br_squeeze_tight": {"signal": "squeeze_break", "params": {"q": 0.15}, "why": "より強い収縮後"},
    "br_volspike": {"signal": "vol_spike", "params": {"mult": 3.0}, "why": "出来高急増の方向に乗る"},
    "br_volspike_fade": {"signal": "vol_spike_fade", "params": {"mult": 3.0}, "why": "出来高急増の逆張り"},
    "br_trend_pb": {"signal": "trend_pullback", "params": {}, "why": "上位足の向きに押し目"},
    "br_session_13": {"signal": "session", "params": {"hour": 13, "side": 1}, "why": "UTC13時ロング"},
    "br_session_13s": {"signal": "session", "params": {"hour": 13, "side": -1}, "why": "UTC13時ショート"},
    "br_session_0": {"signal": "session", "params": {"hour": 0, "side": 1}, "why": "UTC0時ロング"},
    "br_gap_revert": {"signal": "gap_revert", "params": {"k": 8, "thr": 0.008}, "why": "2時間急変の逆張り"},
    "br_gap_revert_lg": {"signal": "gap_revert", "params": {"k": 24, "thr": 0.02}, "why": "6時間急変の逆張り"},
    "br_gap_follow": {"signal": "gap_follow", "params": {"k": 8, "thr": 0.008}, "why": "2時間急変の順張り"},
    "br_gap_follow_lg": {"signal": "gap_follow", "params": {"k": 24, "thr": 0.02}, "why": "6時間急変の順張り"},
    "br_fund_cheap": {
        "signal": "funding_side", "params": {"mode": "cheap", "thr": 0.0001},
        "why": "funding が安い方向に乗る", "needs_deriv": True,
    },
    "br_fund_fade": {
        "signal": "funding_side", "params": {"mode": "crowded", "thr": 0.0001},
        "why": "funding が高い（混み合い）方向に乗る", "needs_deriv": True,
    },
    "br_oi_follow": {
        "signal": "oi_follow", "params": {"n": 16, "thr": 0.005},
        "why": "OI増加の方向に乗る", "needs_deriv": True,
    },
    "br_oi_fade": {
        "signal": "oi_fade", "params": {"n": 16, "thr": 0.01},
        "why": "OI急増の逆張り", "needs_deriv": True,
    },
    "br_taker_follow": {
        "signal": "taker_follow", "params": {"q": 0.8},
        "why": "taker 優勢の方向に乗る", "needs_deriv": True,
    },
    "br_taker_fade": {
        "signal": "taker_fade", "params": {"q": 0.8},
        "why": "taker 優勢の逆張り", "needs_deriv": True,
    },
    "br_basis_fade": {
        "signal": "basis_fade", "params": {"q": 0.9},
        "why": "プレミアム極端の逆張り", "needs_deriv": True,
    },
    "br_runs5_fund": {
        "signal": "runs_funding", "params": {"k": 5, "thr": 0.0001},
        "why": "5連続継続 × funding安い側（one-point）", "needs_deriv": True,
    },
}


def build_signals(logic_id: str, df: pd.DataFrame, cycle: dict | None = None) -> np.ndarray:
    spec = (cycle or CYCLE_BRACKET)[logic_id]
    return SIGNALS[spec["signal"]](df, spec.get("params") or {}).values


_BAR_COUNT_KEYS = ("fast", "slow", "window", "n", "look", "k", "rsi")


def cycle_bracket_1m() -> dict[str, dict]:
    """15分足と同じ時間窓になるよう、バー数を ×15 した OHLCV 条件。

    派生データは15分グリッド前提なので、1分足の最初の検証からは外す。
    """
    out: dict[str, dict] = {}
    for logic_id, spec in CYCLE_BRACKET.items():
        if spec.get("needs_deriv"):
            continue
        params = dict(spec.get("params") or {})
        signal = spec["signal"]
        if signal == "rsi_revert":
            params.setdefault("n", 14)
        elif signal == "trend_pullback":
            params.setdefault("slow", 192)
            params.setdefault("fast", 12)
            params.setdefault("rsi", 14)
        elif signal == "squeeze_break":
            params.setdefault("n", 14)
            params.setdefault("look", 96)
            params.setdefault("window", 12)
        elif signal in ("vol_spike", "vol_spike_fade"):
            params.setdefault("look", 96)
        scaled = {}
        for key, value in params.items():
            if key in _BAR_COUNT_KEYS and isinstance(value, int):
                # 連続足の本数 k は1分足ネイティブ（5本=5分）。時間換算すると
                # 75本連続になり、以前の br_runs_5 とは別物でほとんど発火しない。
                if signal in ("runs", "runs_fade") and key == "k":
                    scaled[key] = value
                else:
                    scaled[key] = value * M15_TO_1M
            else:
                scaled[key] = value
        out[logic_id] = {**spec, "params": scaled}
    out["br_runs_5_15m"] = {
        "signal": "runs_resampled",
        "params": {"k": 5, "rule": "15min"},
        "why": "5連続15分足の継続（決済だけ1分足）",
    }
    return out
