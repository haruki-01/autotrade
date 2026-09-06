"""Phase0 shared utilities: GMO data, sessions, SPIKE detection."""

from __future__ import annotations

import time
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

JST = ZoneInfo("Asia/Tokyo")
GMO_PUBLIC = "https://api.coin.z.com/public"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CACHE_PATH = DATA_DIR / "btc_jpy_5m.parquet"

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)

SESSIONS = {
    "TOKYO": (9, 15),
    "EUROPE_US": (16, 24),
    "OFF": None,
}


def fetch_klines_day(symbol: str, interval: str, day: date, retries: int = 4) -> list[dict]:
    params = {
        "symbol": symbol,
        "interval": interval,
        "date": day.strftime("%Y%m%d"),
    }
    for attempt in range(retries):
        try:
            resp = requests.get(f"{GMO_PUBLIC}/v1/klines", params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("status") == 0:
                return payload.get("data", [])
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    return []


def fetch_btc_jpy_5m(start: date, end: date, sleep_s: float = 0.15) -> pd.DataFrame:
    rows: list[dict] = []
    day = start
    total_days = (end - start).days + 1
    fetched = 0
    while day <= end:
        for bar in fetch_klines_day("BTC_JPY", "5min", day):
            ts = pd.Timestamp(int(bar["openTime"]), unit="ms", tz="UTC").tz_convert(JST)
            rows.append(
                {
                    "open_time": ts,
                    "open": float(bar["open"]),
                    "high": float(bar["high"]),
                    "low": float(bar["low"]),
                    "close": float(bar["close"]),
                    "volume": float(bar["volume"]),
                }
            )
        fetched += 1
        if fetched % 50 == 0:
            print(f"  fetched {fetched}/{total_days} days...", flush=True)
        day += timedelta(days=1)
        time.sleep(sleep_s)

    df = pd.DataFrame(rows).sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)
    df["range"] = df["high"] - df["low"]
    df["ret"] = df["close"].pct_change()
    df["body"] = (df["close"] - df["open"]).abs()
    return df


def load_or_fetch(start: date, end: date, force: bool = False) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists() and not force:
        df = pd.read_parquet(CACHE_PATH)
        df["open_time"] = pd.to_datetime(df["open_time"], utc=True).dt.tz_convert(JST)
        mask = (df["open_time"] >= pd.Timestamp(start, tz=JST)) & (
            df["open_time"] <= pd.Timestamp(end, tz=JST) + pd.Timedelta(hours=23, minutes=55)
        )
        return df.loc[mask].reset_index(drop=True)

    print(f"Fetching BTC_JPY 5m from GMO: {start} .. {end}")
    df = fetch_btc_jpy_5m(start, end)
    df.to_parquet(CACHE_PATH, index=False)
    print(f"Cached {len(df)} bars -> {CACHE_PATH}")
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["hour"] = out["open_time"].dt.hour
    out["minute"] = out["open_time"].dt.minute
    out["weekday"] = out["open_time"].dt.weekday  # 0=Mon
    out["is_weekend"] = out["weekday"] >= 5

    def session_label(row: pd.Series) -> str:
        h = row["hour"]
        if 9 <= h < 15:
            return "TOKYO"
        if 16 <= h < 24:
            return "EUROPE_US"
        return "OFF"

    out["session"] = out.apply(session_label, axis=1)

    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - out["close"].shift(1)).abs(),
            (out["low"] - out["close"].shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr14"] = tr.rolling(14, min_periods=14).mean()

    out["fwd_ret_12"] = out["close"].shift(-12) / out["close"] - 1
    out["range_med100"] = out["range"].rolling(100, min_periods=100).median()

    roll_high = out["high"].rolling(24, min_periods=24).max().shift(1)
    roll_low = out["low"].rolling(24, min_periods=24).min().shift(1)
    break_up = out["close"] > roll_high
    break_down = out["close"] < roll_low
    break_width = np.where(break_up, out["close"] - roll_high, np.where(break_down, roll_low - out["close"], 0))
    range_spike = out["range"] >= out["range_med100"] * 2.5
    atr_ok = break_width >= 0.4 * out["atr14"]
    out["is_spike"] = (break_up | break_down) & range_spike & atr_ok
    out["spike_dir"] = np.where(break_up, 1, np.where(break_down, -1, 0))

    cont_fail = np.where(
        out["is_spike"],
        np.where(
            out["spike_dir"] == 1,
            out["fwd_ret_12"] <= 0,
            out["fwd_ret_12"] >= 0,
        ),
        np.nan,
    )
    out["spike_cont_fail"] = cont_fail

    out["fwd_ret_3"] = out["close"].shift(-3) / out["close"] - 1
    out["fwd_ret_24"] = out["close"].shift(-24) / out["close"] - 1
    out["fwd_ret_48"] = out["close"].shift(-48) / out["close"] - 1
    out["body_med100"] = out["body"].rolling(100, min_periods=100).median()
    out["rv_20"] = out["ret"].rolling(20, min_periods=20).std()

    delta = out["close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(14, min_periods=14).mean()
    avg_loss = loss.rolling(14, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out["rsi14"] = 100 - (100 / (1 + rs))

    return out


def resample_ohlc(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    tmp = df.set_index("open_time")
    ohlc = tmp.resample(freq).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    ohlc = ohlc.dropna(subset=["open"]).reset_index()
    ohlc["range"] = ohlc["high"] - ohlc["low"]
    ohlc["ret"] = ohlc["close"].pct_change()
    ohlc["body"] = (ohlc["close"] - ohlc["open"]).abs()
    return ohlc


def merge_htf(df: pd.DataFrame) -> pd.DataFrame:
    """Attach 1h and 12h EMA regime to 5m bars."""
    out = df.copy()
    h1 = resample_ohlc(out, "1h")
    h12 = resample_ohlc(out, "12h")
    h1["ema20"] = h1["close"].ewm(span=20, adjust=False).mean()
    h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
    h12["ema20"] = h12["close"].ewm(span=20, adjust=False).mean()
    h12["ema50"] = h12["close"].ewm(span=50, adjust=False).mean()
    h1["regime"] = np.where(h1["ema20"] > h1["ema50"], 1, np.where(h1["ema20"] < h1["ema50"], -1, 0))
    h12["regime"] = np.where(h12["ema20"] > h12["ema50"], 1, np.where(h12["ema20"] < h12["ema50"], -1, 0))

    out = pd.merge_asof(
        out.sort_values("open_time"),
        h1[["open_time", "ema20", "ema50", "regime"]].rename(
            columns={"ema20": "h1_ema20", "ema50": "h1_ema50", "regime": "h1_regime"}
        ),
        on="open_time",
        direction="backward",
    )
    out = pd.merge_asof(
        out.sort_values("open_time"),
        h12[["open_time", "close", "ema20", "ema50", "regime"]].rename(
            columns={
                "close": "h12_close",
                "ema20": "h12_ema20",
                "ema50": "h12_ema50",
                "regime": "h12_regime",
            }
        ),
        on="open_time",
        direction="backward",
    )
    return out


def spike_revert_edge(df: pd.DataFrame, horizon: str = "h60", mask: pd.Series | None = None) -> pd.Series:
    col = {"h15": "fwd_ret_3", "h60": "fwd_ret_12", "h120": "fwd_ret_24" if "fwd_ret_24" in df else "fwd_ret_12", "h240": "fwd_ret_48"}.get(
        horizon, "fwd_ret_12"
    )
    sub = df.loc[df["is_spike"]] if mask is None else df.loc[df["is_spike"] & mask]
    edge = np.where(sub["spike_dir"] == 1, -sub[col], sub[col])
    return pd.Series(edge, index=sub.index).dropna()


def spike_cont_edge(df: pd.DataFrame, horizon: str = "h60", mask: pd.Series | None = None) -> pd.Series:
    col = {"h15": "fwd_ret_3", "h60": "fwd_ret_12", "h240": "fwd_ret_48"}.get(horizon, "fwd_ret_12")
    sub = df.loc[df["is_spike"]] if mask is None else df.loc[df["is_spike"] & mask]
    edge = np.where(sub["spike_dir"] == 1, sub[col], -sub[col])
    return pd.Series(edge, index=sub.index).dropna()


def metric_from_series(r: pd.Series, vs_baseline: float | None = None, min_n: int = 100, notes: str = "") -> dict:
    stats = summarize_returns(r)
    stats["vs_baseline"] = vs_baseline
    stats["verdict"] = verdict_from_stats(stats, vs_baseline, min_n=min_n)
    stats["notes"] = notes
    return stats


def detect_vol_shock(df: pd.DataFrame) -> pd.DataFrame:
    """Mark VOL_SHOCK per phase0-stats HELPER-VOL (rv top 10% or range spike)."""
    out = df.copy()
    rv = out["rv_20"]
    rv_threshold = rv.rolling(2880, min_periods=500).quantile(0.90)
    range_spike = out["range"] >= out["range_med100"] * 2.5
    rv_spike = rv >= rv_threshold
    out["is_vol_shock"] = (rv_spike | range_spike) & out["range_med100"].notna()
    out["shock_dir"] = np.where(
        out["close"] > out["open"],
        1,
        np.where(out["close"] < out["open"], -1, 0),
    )
    return out


def detect_ignite(df: pd.DataFrame) -> pd.DataFrame:
    """Mark IGNITE events at 3rd bar of 3 consecutive same-direction candles."""
    out = df.copy()
    up = (out["close"] > out["open"]) & (out["body"] >= out["body_med100"] * 1.5)
    down = (out["close"] < out["open"]) & (out["body"] >= out["body_med100"] * 1.5)
    out["up_streak"] = up.groupby((~up).cumsum()).cumcount() + 1
    out["down_streak"] = down.groupby((~down).cumsum()).cumcount() + 1
    out["is_ignite_up"] = up & (out["up_streak"] == 3)
    out["is_ignite_down"] = down & (out["down_streak"] == 3)
    out["is_ignite"] = out["is_ignite_up"] | out["is_ignite_down"]
    out["ignite_dir"] = np.where(out["is_ignite_up"], 1, np.where(out["is_ignite_down"], -1, 0))
    return out


def ignite_edge(df: pd.DataFrame, indices: pd.Index, col: str = "fwd_ret_48") -> pd.Series:
    sub = df.loc[indices]
    edge = np.where(sub["ignite_dir"] == 1, sub[col], -sub[col])
    return pd.Series(edge, index=indices).dropna()


def months_in_sample(df: pd.DataFrame) -> float:
    days = (df["open_time"].max() - df["open_time"].min()).days
    return max(days / 30.44, 1)


def in_time_range(ts: pd.Timestamp, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    t = ts.hour * 60 + ts.minute
    start = start_h * 60 + start_m
    end = end_h * 60 + end_m
    return start <= t < end


def window_mask(df: pd.DataFrame, start_h: int, start_m: int, end_h: int, end_m: int) -> pd.Series:
    mins = df["open_time"].dt.hour * 60 + df["open_time"].dt.minute
    start = start_h * 60 + start_m
    end = end_h * 60 + end_m
    return (mins >= start) & (mins < end)


def summarize_returns(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) == 0:
        return {"n": 0, "hit_rate": np.nan, "mean_edge": np.nan, "median_edge": np.nan, "p25": np.nan, "p75": np.nan, "mean_abs_move": np.nan}
    return {
        "n": int(len(r)),
        "hit_rate": float((r > 0).mean()),
        "mean_edge": float(r.mean()),
        "median_edge": float(r.median()),
        "p25": float(r.quantile(0.25)),
        "p75": float(r.quantile(0.75)),
        "mean_abs_move": float(r.abs().mean()),
    }


def verdict_from_stats(stats: dict, vs_baseline: float | None, min_n: int = 100) -> str:
    n = stats.get("n", 0)
    if n < min_n:
        return "insufficient_n"
    mean_e = stats.get("mean_edge", np.nan)
    hit = stats.get("hit_rate", np.nan)
    if np.isnan(mean_e):
        return "insufficient_n"
    if vs_baseline is not None and abs(vs_baseline) < 0.00005 and hit is not None and abs(hit - 0.5) < 0.02:
        return "fail"
    if vs_baseline is not None and vs_baseline > 0.0001 and hit >= 0.55:
        return "pass"
    if vs_baseline is not None and vs_baseline > 0:
        return "weak"
    if mean_e > 0 and hit >= 0.55:
        return "pass"
    if mean_e > 0:
        return "weak"
    return "fail"
