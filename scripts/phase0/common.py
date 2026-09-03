"""Phase0 shared utilities: GMO data, sessions, SPIKE detection."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

JST = ZoneInfo("Asia/Tokyo")
GMO_PUBLIC = "https://api.coin.z.com/public"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CACHE_PATH = DATA_DIR / "btc_jpy_5m.parquet"

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
    return out


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
