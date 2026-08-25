"""ADV-001 / 002 / 004 / 005 の入口。上位足は確定後のみ。1分はトリガーだけ。"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from autotrade.strategy.bracket import Signals, _resample_ohlc


def _h15(df: pd.DataFrame) -> pd.DataFrame:
    return _resample_ohlc(df, "15min")


def _h1h(df: pd.DataFrame) -> pd.DataFrame:
    return _resample_ohlc(df, "60min")


def _complete_ts(bar_start: pd.Timestamp, minutes: int) -> pd.Timestamp:
    return bar_start + pd.Timedelta(minutes=minutes - 1)


def _search(index: pd.DatetimeIndex, ts: pd.Timestamp) -> int:
    i = int(index.searchsorted(ts))
    if i >= len(index):
        return -1
    return i


def _stamp(sig: np.ndarray, index: pd.DatetimeIndex, ts: pd.Timestamp, direction: int) -> None:
    i = _search(index, ts)
    if i >= 0:
        sig[i] = np.int8(direction)


def _first_retest(
    df: pd.DataFrame,
    start: pd.Timestamp,
    *,
    direction: int,
    level: float,
    band: float,
    max_minutes: int,
    sig: np.ndarray,
) -> None:
    """確定後、水準を触れて外側で終えた最初の1分。"""
    idx = df.index
    i0 = _search(idx, start)
    if i0 < 0:
        return
    close = df["close"].to_numpy(float)
    low = df["low"].to_numpy(float)
    high = df["high"].to_numpy(float)
    end = min(len(df), i0 + max_minutes)
    for i in range(i0, end):
        if direction > 0:
            if low[i] <= level * (1 + band) and close[i] > level:
                sig[i] = 1
                return
        else:
            if high[i] >= level * (1 - band) and close[i] < level:
                sig[i] = -1
                return


def sig_adv002(df: pd.DataFrame, p: dict) -> Signals:
    """1時間未認定 + 下位の失敗下抜けを取り戻してから入る。"""
    k_1h = int(p.get("k_1h", 6))
    rec_bars = int(p.get("rec_bars", 2))
    min_depth = float(p.get("min_depth", 0.0))
    side = str(p.get("side", "both"))
    trigger = str(p.get("trigger", "1m_cross"))  # 1m_cross | reclaim_close
    native_1m = bool(p.get("native_1m", False))
    n_1m = int(p.get("n_1m", 15))
    rec_1m = int(p.get("rec_1m", 10))

    sig = np.zeros(len(df), dtype=np.int8)
    h15 = _h15(df)
    h1h = _h1h(df)
    if h15.empty or h1h.empty:
        return Signals(sig)

    roll = h1h["high"].shift(1).rolling(k_1h, min_periods=k_1h).max()
    no_hh = h1h["high"] < roll
    roll_l = h1h["low"].shift(1).rolling(k_1h, min_periods=k_1h).min()
    no_ll = h1h["low"] > roll_l
    h1h = h1h.assign(no_hh=no_hh.astype(float), no_ll=no_ll.astype(float))
    h1h_c = h1h.copy()
    h1h_c.index = h1h.index + pd.Timedelta(minutes=59)
    no_hh_a = h1h_c["no_hh"].reindex(h15.index, method="ffill").fillna(0).to_numpy(float)
    no_ll_a = h1h_c["no_ll"].reindex(h15.index, method="ffill").fillna(0).to_numpy(float)

    if native_1m:
        return _adv002_native(df, sig, no_hh_a, no_ll_a, h15, p, n_1m, rec_1m, side, min_depth)

    high = h15["high"].to_numpy(float)
    low = h15["low"].to_numpy(float)
    close = h15["close"].to_numpy(float)
    n = len(h15)
    for i in range(1, n - 1):
        # down sweep → long
        if side != "short" and no_hh_a[i] > 0.5:
            if low[i] < low[i - 1] * (1 - min_depth):
                swept = low[i - 1]
                sweep_px = high[i]
                for j in range(i + 1, min(i + 1 + rec_bars, n)):
                    if low[j] < low[i]:
                        break
                    if close[j] > swept:
                        t0 = _complete_ts(h15.index[j], 15)
                        if trigger == "reclaim_close":
                            _stamp(sig, df.index, t0, 1)
                        else:
                            _first_retest(
                                df, t0, direction=1, level=sweep_px, band=0.0002,
                                max_minutes=int(p.get("max_minutes", 180)), sig=sig,
                            )
                        break
        # up sweep → short
        if side != "long" and no_ll_a[i] > 0.5:
            if high[i] > high[i - 1] * (1 + min_depth):
                swept = high[i - 1]
                sweep_px = low[i]
                for j in range(i + 1, min(i + 1 + rec_bars, n)):
                    if high[j] > high[i]:
                        break
                    if close[j] < swept:
                        t0 = _complete_ts(h15.index[j], 15)
                        if trigger == "reclaim_close":
                            _stamp(sig, df.index, t0, -1)
                        else:
                            _first_retest(
                                df, t0, direction=-1, level=sweep_px, band=0.0002,
                                max_minutes=int(p.get("max_minutes", 180)), sig=sig,
                            )
                        break
    return Signals(sig)


def _adv002_native(
    df: pd.DataFrame,
    sig: np.ndarray,
    no_hh_a: np.ndarray,
    no_ll_a: np.ndarray,
    h15: pd.DataFrame,
    p: dict,
    n_1m: int,
    rec_1m: int,
    side: str,
    min_depth: float,
) -> Signals:
    """スイープを1分で測る変種。1時間未認定は確定15分へffillしたフラグを1分へ載せる。"""
    no_hh = pd.Series(no_hh_a, index=h15.index)
    no_hh.index = h15.index + pd.Timedelta(minutes=14)
    no_hh_1m = no_hh.reindex(df.index, method="ffill").fillna(0).to_numpy(float)
    no_ll = pd.Series(no_ll_a, index=h15.index)
    no_ll.index = h15.index + pd.Timedelta(minutes=14)
    no_ll_1m = no_ll.reindex(df.index, method="ffill").fillna(0).to_numpy(float)
    low = df["low"].to_numpy(float)
    high = df["high"].to_numpy(float)
    close = df["close"].to_numpy(float)
    n = len(df)
    prior_l = pd.Series(low).shift(1).rolling(n_1m, min_periods=n_1m).min().to_numpy()
    prior_h = pd.Series(high).shift(1).rolling(n_1m, min_periods=n_1m).max().to_numpy()
    for i in range(n_1m + 1, n - 1):
        if side != "short" and no_hh_1m[i] > 0.5 and low[i] < prior_l[i] * (1 - min_depth):
            swept = prior_l[i]
            px = high[i]
            for j in range(i + 1, min(i + 1 + rec_1m, n)):
                if low[j] < low[i]:
                    break
                if close[j] > swept:
                    _first_retest(
                        df, df.index[j], direction=1, level=px, band=0.0002,
                        max_minutes=int(p.get("max_minutes", 60)), sig=sig,
                    )
                    break
        if side != "long" and no_ll_1m[i] > 0.5 and high[i] > prior_h[i] * (1 + min_depth):
            swept = prior_h[i]
            px = low[i]
            for j in range(i + 1, min(i + 1 + rec_1m, n)):
                if high[j] > high[i]:
                    break
                if close[j] < swept:
                    _first_retest(
                        df, df.index[j], direction=-1, level=px, band=0.0002,
                        max_minutes=int(p.get("max_minutes", 60)), sig=sig,
                    )
                    break
    return Signals(sig)


def sig_adv001(df: pd.DataFrame, p: dict) -> Signals:
    """定番の初回抜け失敗のあと、本突破確定→箱縁の1分触れ。"""
    box_n = int(p.get("box_n", 8))
    fail_max = int(p.get("fail_max", 2))
    wait_after = int(p.get("wait_after", 0))
    min_width = float(p.get("min_width", 0.0))
    asia_only = bool(p.get("asia_only", False))
    side = str(p.get("side", "both"))
    trigger = str(p.get("trigger", "1m_retest"))
    band = float(p.get("band", 0.0003))
    max_minutes = int(p.get("max_minutes", 240))

    sig = np.zeros(len(df), dtype=np.int8)
    h15 = _h15(df)
    if len(h15) < box_n + 6:
        return Signals(sig)
    high = h15["high"].to_numpy(float)
    low = h15["low"].to_numpy(float)
    close = h15["close"].to_numpy(float)
    hours = h15.index.hour
    n = len(h15)
    i = box_n
    while i < n - 2:
        if asia_only and not (0 <= hours[i] < 8):
            i += 1
            continue
        box_h = float(np.max(high[i - box_n : i]))
        box_l = float(np.min(low[i - box_n : i]))
        width = (box_h - box_l) / box_l if box_l else 0.0
        if width < min_width:
            i += 1
            continue
        # first break up
        if side != "short" and close[i] > box_h:
            failed = False
            k_fail = None
            for k in range(i + 1, min(i + 1 + fail_max, n)):
                if close[k] < box_h:
                    failed = True
                    k_fail = k
                    break
                if close[k] > box_h * 1.01:
                    break
            if failed and k_fail is not None:
                real = None
                for m in range(k_fail + 1, min(k_fail + 1 + 16, n)):
                    if close[m] > box_h:
                        real = m
                        break
                    if close[m] < box_l:
                        break
                if real is not None:
                    use = real + wait_after
                    if use < n:
                        t0 = _complete_ts(h15.index[use], 15)
                        if trigger == "real_close":
                            _stamp(sig, df.index, t0, 1)
                        else:
                            _first_retest(
                                df, t0, direction=1, level=box_h, band=band,
                                max_minutes=max_minutes, sig=sig,
                            )
                        i = use + 1
                        continue
        if side != "long" and close[i] < box_l:
            failed = False
            k_fail = None
            for k in range(i + 1, min(i + 1 + fail_max, n)):
                if close[k] > box_l:
                    failed = True
                    k_fail = k
                    break
            if failed and k_fail is not None:
                real = None
                for m in range(k_fail + 1, min(k_fail + 1 + 16, n)):
                    if close[m] < box_l:
                        real = m
                        break
                    if close[m] > box_h:
                        break
                if real is not None:
                    use = real + wait_after
                    if use < n:
                        t0 = _complete_ts(h15.index[use], 15)
                        if trigger == "real_close":
                            _stamp(sig, df.index, t0, -1)
                        else:
                            _first_retest(
                                df, t0, direction=-1, level=box_l, band=band,
                                max_minutes=max_minutes, sig=sig,
                            )
                        i = use + 1
                        continue
        i += 1
    return Signals(sig)


def sig_adv005(df: pd.DataFrame, p: dict) -> Signals:
    """アジア箱が厚い時間の15分終値で折れたあと、縁の維持だけ取る。"""
    asia_end = int(p.get("asia_end", 8))
    min_hour = int(p.get("min_hour", 7))
    min_touches = int(p.get("min_touches", 2))
    max_width = float(p.get("max_width", 0.012))
    use_width = bool(p.get("use_width", True))
    accept = str(p.get("accept", "15m"))  # 15m | 1h
    window_h = int(p.get("window_h", 8))
    side = str(p.get("side", "both"))
    first_print = bool(p.get("first_print", False))
    band = float(p.get("band", 0.0004))

    sig = np.zeros(len(df), dtype=np.int8)
    h15 = _h15(df)
    if h15.empty:
        return Signals(sig)
    h15 = h15.copy()
    h15["date"] = h15.index.tz_convert("UTC").date
    high = h15["high"].to_numpy(float)
    low = h15["low"].to_numpy(float)
    close = h15["close"].to_numpy(float)
    hour = np.asarray(h15.index.hour)

    for day, g in h15.groupby("date"):
        loc = g.index
        sl = h15.index.get_indexer(loc)
        asia_mask = (hour[sl] >= 0) & (hour[sl] < asia_end)
        if asia_mask.sum() < 4:
            continue
        a_i = sl[asia_mask]
        box_h = float(np.max(high[a_i]))
        box_l = float(np.min(low[a_i]))
        if box_l <= 0:
            continue
        width = (box_h - box_l) / box_l
        if use_width and width > max_width:
            continue
        touch_h = int(np.sum(np.abs(high[a_i] - box_h) / box_h < 0.0008))
        touch_l = int(np.sum(np.abs(low[a_i] - box_l) / box_l < 0.0008))
        after = sl[(hour[sl] >= min_hour)]
        if after.size == 0:
            continue
        # accept up
        if side != "short" and touch_h >= min_touches:
            acc = None
            for j in after:
                if close[j] > box_h:
                    if accept == "1h" and int(h15.index[j].minute) != 45:
                        continue
                    acc = j
                    break
            if acc is not None:
                t0 = _complete_ts(h15.index[acc], 15)
                if first_print:
                    _stamp(sig, df.index, t0, 1)
                else:
                    _first_retest(
                        df, t0, direction=1, level=box_h, band=band,
                        max_minutes=window_h * 60, sig=sig,
                    )
        if side != "long" and touch_l >= min_touches:
            acc = None
            for j in after:
                if close[j] < box_l:
                    if accept == "1h" and h15.index[j].minute != 45:
                        continue
                    acc = j
                    break
            if acc is not None:
                t0 = _complete_ts(h15.index[acc], 15)
                if first_print:
                    _stamp(sig, df.index, t0, -1)
                else:
                    _first_retest(
                        df, t0, direction=-1, level=box_l, band=band,
                        max_minutes=window_h * 60, sig=sig,
                    )
    return Signals(sig)


def apply_retail_veto(sig: np.ndarray, acct: pd.Series, p: dict) -> np.ndarray:
    """個人多数側の方向を落とす。acct_ratio は long/short。"""
    out = sig.copy()
    mode = str(p.get("veto_mode", "acct_thr"))
    thr = float(p.get("thr", 1.2))
    z_thr = float(p.get("z_thr", 1.0))
    invert = bool(p.get("invert", False))
    a = acct.astype(float)
    if mode == "zscore":
        win = int(p.get("z_win", 96))
        mu = a.rolling(win, min_periods=win).mean()
        sd = a.rolling(win, min_periods=win).std()
        z = (a - mu) / sd.replace(0, np.nan)
        long_block = z > z_thr
        short_block = z < -z_thr
    else:
        long_block = a > thr
        short_block = a < (1.0 / thr if thr else 0.8)
    long_block = long_block.fillna(False).to_numpy()
    short_block = short_block.fillna(False).to_numpy()
    if invert:
        long_block, short_block = short_block, long_block
    out[(out == 1) & long_block] = 0
    out[(out == -1) & short_block] = 0
    return out


def sig_adv004(df: pd.DataFrame, p: dict) -> Signals:
    host = str(p.get("host", "adv002"))
    if host == "adv001":
        raw = sig_adv001(df, p.get("host_params") or {"box_n": 8, "fail_max": 2})
    elif host == "adv005":
        raw = sig_adv005(df, p.get("host_params") or {"asia_end": 8, "min_touches": 2})
    else:
        raw = sig_adv002(df, p.get("host_params") or {"k_1h": 6, "rec_bars": 2})
    col = str(p.get("ratio_col", "acct_ratio"))
    if col not in df.columns:
        return Signals(np.zeros(len(df), dtype=np.int8))
    # 15分確定値だけ使う: 未完成の5分を1分に載せないよう、15分グリッドへ落としてからffill
    s = df[col].astype(float)
    h15 = s.resample("15min", label="left", closed="left").last()
    h15.index = h15.index + pd.Timedelta(minutes=14)
    aligned = h15.reindex(df.index, method="ffill")
    return Signals(apply_retail_veto(raw.values, aligned, p))


SIGNALS_ADV: dict[str, Callable[[pd.DataFrame, dict], Signals]] = {
    "adv001": sig_adv001,
    "adv002": sig_adv002,
    "adv004": sig_adv004,
    "adv005": sig_adv005,
}


# 各ファミリ10変種。1点差分。検証前に固定。
CYCLES_ADV: dict[str, list[dict]] = {
    "adv002": [
        {"id": "adv002_r00", "params": {"k_1h": 6, "rec_bars": 2}, "why": "基準: 1h未HH 6本、15分取り戻し2本、1分再テスト"},
        {"id": "adv002_r01", "params": {"k_1h": 12, "rec_bars": 2}, "why": "1h未HHを12本に延長"},
        {"id": "adv002_r02", "params": {"k_1h": 3, "rec_bars": 2}, "why": "1h未HHを3本に短縮"},
        {"id": "adv002_r03", "params": {"k_1h": 6, "rec_bars": 1}, "why": "取り戻しを翌15分だけに"},
        {"id": "adv002_r04", "params": {"k_1h": 6, "rec_bars": 4}, "why": "取り戻し猶予を4本に"},
        {"id": "adv002_r05", "params": {"k_1h": 6, "rec_bars": 2, "trigger": "reclaim_close"}, "why": "1分再テストをやめ、取り戻し15分の確定1分で入る"},
        {"id": "adv002_r06", "params": {"k_1h": 6, "rec_bars": 2, "min_depth": 0.001}, "why": "スイープ深さ0.10%以上"},
        {"id": "adv002_r07", "params": {"k_1h": 6, "rec_bars": 2, "side": "long"}, "why": "ロングだけ（下の失敗）"},
        {"id": "adv002_r08", "params": {"k_1h": 6, "rec_bars": 2, "max_minutes": 60}, "why": "再テスト待ちを60分に制限"},
        {"id": "adv002_r09", "params": {"native_1m": True, "k_1h": 6, "n_1m": 15, "rec_1m": 10}, "why": "スイープを1分ネイティブに（実証①）"},
    ],
    "adv001": [
        {"id": "adv001_r00", "params": {"box_n": 8, "fail_max": 2}, "why": "基準: 8本箱、失敗2本以内、1分リテスト"},
        {"id": "adv001_r01", "params": {"box_n": 16, "fail_max": 2}, "why": "箱を16本に"},
        {"id": "adv001_r02", "params": {"box_n": 4, "fail_max": 2}, "why": "箱を4本に"},
        {"id": "adv001_r03", "params": {"box_n": 8, "fail_max": 1}, "why": "失敗を翌15分だけに"},
        {"id": "adv001_r04", "params": {"box_n": 8, "fail_max": 4}, "why": "失敗猶予を4本に"},
        {"id": "adv001_r05", "params": {"box_n": 8, "fail_max": 2, "trigger": "real_close"}, "why": "リテストをやめ本突破15分確定で入る"},
        {"id": "adv001_r06", "params": {"box_n": 8, "fail_max": 2, "min_width": 0.004}, "why": "箱幅0.40%以上"},
        {"id": "adv001_r07", "params": {"box_n": 8, "fail_max": 2, "asia_only": True}, "why": "アジア時間の箱だけ"},
        {"id": "adv001_r08", "params": {"box_n": 8, "fail_max": 2, "side": "long"}, "why": "上方向だけ"},
        {"id": "adv001_r09", "params": {"box_n": 8, "fail_max": 2, "wait_after": 1}, "why": "本突破の翌15分まで待つ"},
    ],
    "adv005": [
        {"id": "adv005_r00", "params": {"asia_end": 8, "min_touches": 2, "use_width": True, "max_width": 0.012}, "why": "基準: アジア0-8、接触2、幅1.2%、15分確定後リテスト"},
        {"id": "adv005_r01", "params": {"asia_end": 8, "min_touches": 2, "use_width": False}, "why": "幅フィルタを外す"},
        {"id": "adv005_r02", "params": {"asia_end": 8, "min_touches": 2, "accept": "1h"}, "why": "受け入れを1時間終値に"},
        {"id": "adv005_r03", "params": {"asia_end": 6, "min_touches": 2}, "why": "アジア箱を0-6時に"},
        {"id": "adv005_r04", "params": {"asia_end": 8, "min_touches": 3}, "why": "接触3回以上"},
        {"id": "adv005_r05", "params": {"asia_end": 8, "min_touches": 1}, "why": "接触1回で箱とみなす"},
        {"id": "adv005_r06", "params": {"asia_end": 8, "min_touches": 2, "window_h": 4}, "why": "確定後の入口を4時間以内に"},
        {"id": "adv005_r07", "params": {"asia_end": 8, "min_touches": 2, "window_h": 12}, "why": "確定後の入口を12時間まで"},
        {"id": "adv005_r08", "params": {"asia_end": 8, "min_touches": 2, "side": "long"}, "why": "上割れだけ"},
        {"id": "adv005_r09", "params": {"asia_end": 8, "min_touches": 2, "max_width": 0.006}, "why": "幅上限を0.60%に"},
    ],
    "adv004": [
        {"id": "adv004_r00", "params": {"host": "adv002", "thr": 1.2, "veto_mode": "acct_thr"}, "why": "基準: ADV-002ホスト、個人比>1.2でロング拒否"},
        {"id": "adv004_r01", "params": {"host": "adv002", "thr": 1.5, "veto_mode": "acct_thr"}, "why": "閾値1.5"},
        {"id": "adv004_r02", "params": {"host": "adv002", "thr": 2.0, "veto_mode": "acct_thr"}, "why": "閾値2.0"},
        {"id": "adv004_r03", "params": {"host": "adv002", "thr": 1.1, "veto_mode": "acct_thr"}, "why": "閾値1.1（厳しく）"},
        {"id": "adv004_r04", "params": {"host": "adv002", "z_thr": 1.0, "veto_mode": "zscore"}, "why": "z>1で拒否"},
        {"id": "adv004_r05", "params": {"host": "adv002", "z_thr": 2.0, "veto_mode": "zscore"}, "why": "z>2で拒否"},
        {"id": "adv004_r06", "params": {"host": "adv001", "thr": 1.2, "veto_mode": "acct_thr"}, "why": "ホストをADV-001に"},
        {"id": "adv004_r07", "params": {"host": "adv005", "thr": 1.2, "veto_mode": "acct_thr"}, "why": "ホストをADV-005に"},
        {"id": "adv004_r08", "params": {"host": "adv002", "thr": 1.2, "invert": True}, "why": "符号反転対照（個人側に付く）"},
        {"id": "adv004_r09", "params": {"host": "adv002", "thr": 1.2, "host_params": {"k_1h": 6, "rec_bars": 2, "side": "long"}}, "why": "ホストをロングだけにして拒否"},
    ],
}


def cycle_adv() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for fam, rows in CYCLES_ADV.items():
        fn = {"adv001": "adv001", "adv002": "adv002", "adv004": "adv004", "adv005": "adv005"}[fam]
        for row in rows:
            spec: dict = {"signal": fn, "params": row["params"], "why": row["why"]}
            if fam == "adv004":
                spec["needs_deriv"] = True
            out[row["id"]] = spec
    return out
