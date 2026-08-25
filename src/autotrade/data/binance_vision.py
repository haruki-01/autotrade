from __future__ import annotations

import time
from pathlib import Path

import httpx
import pandas as pd

from autotrade.data.bybit import COLUMNS, load_ohlcv, save_ohlcv

# Spot klines on Binance Vision (reachable from geo-restricted Cloud agents).
# Used as a research fallback when Bybit public API is blocked.
# Prices are BTCUSDT; not identical to Bybit linear, but usable for hypothesis screening.
INTERVAL_MAP = {
    "1m": "1m",
    "15m": "15m",
    "4h": "4h",
    "1d": "1d",
}

BASE_URL = "https://data-api.binance.vision"


class BinanceVisionClient:
    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        binance_interval = INTERVAL_MAP.get(interval, interval)
        rows: list[list] = []
        cursor_start = start_ms

        with httpx.Client(timeout=self.timeout) as client:
            while True:
                params: dict[str, str | int] = {
                    "symbol": symbol,
                    "interval": binance_interval,
                    "limit": limit,
                }
                if cursor_start is not None:
                    params["startTime"] = cursor_start
                if end_ms is not None:
                    params["endTime"] = end_ms

                resp = client.get(f"{self.base_url}/api/v3/klines", params=params)
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break

                rows.extend(batch)
                last_open = int(batch[-1][0])
                next_start = last_open + 1
                if end_ms is not None and next_start > end_ms:
                    break
                if len(batch) < limit:
                    break
                cursor_start = next_start
                time.sleep(0.05)

        if not rows:
            return pd.DataFrame(columns=COLUMNS)

        # Binance: [open_time, open, high, low, close, volume, close_time, quote_volume, ...]
        parsed = [
            {
                "start_ms": int(r[0]),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "turnover": float(r[7]),
            }
            for r in rows
        ]
        df = pd.DataFrame(parsed)
        df = df.drop_duplicates(subset=["start_ms"]).sort_values("start_ms")
        df["timestamp"] = pd.to_datetime(df["start_ms"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        if start_ms is not None:
            df = df[df["start_ms"] >= start_ms]
        if end_ms is not None:
            df = df[df["start_ms"] <= end_ms]
        return df[COLUMNS]


def ensure_binance_data(
    client: BinanceVisionClient,
    *,
    symbol: str,
    interval: str,
    start: str,
    end: str,
    cache_dir: str | Path,
    force: bool = False,
    category: str = "binance_spot",
) -> pd.DataFrame:
    cache_dir = Path(cache_dir)
    cache_path = cache_dir / f"{symbol}_{category}_{interval}_{start}_{end}.csv"
    if cache_path.exists() and not force:
        return load_ohlcv(cache_path)

    start_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end_ms = int(
        (pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)).timestamp()
        * 1000
    )
    df = client.fetch_klines(symbol, interval, start_ms=start_ms, end_ms=end_ms)
    save_ohlcv(df, cache_path)
    return df


ARCHIVE_BASE = "https://data.binance.vision/data"


def _klines_zip_to_ohlcv(raw: pd.DataFrame) -> pd.DataFrame:
    """Binance Vision kline zip: open_time, open, high, low, close, volume, ..., quote_volume."""
    col0 = raw.columns[0]
    if raw[col0].dtype == object:
        raw = raw.copy()
        raw[col0] = pd.to_numeric(raw[col0], errors="coerce")
    start_ms = raw.iloc[:, 0].astype("int64")
    df = pd.DataFrame(
        {
            "start_ms": start_ms,
            "open": pd.to_numeric(raw.iloc[:, 1], errors="coerce"),
            "high": pd.to_numeric(raw.iloc[:, 2], errors="coerce"),
            "low": pd.to_numeric(raw.iloc[:, 3], errors="coerce"),
            "close": pd.to_numeric(raw.iloc[:, 4], errors="coerce"),
            "volume": pd.to_numeric(raw.iloc[:, 5], errors="coerce"),
            "turnover": pd.to_numeric(raw.iloc[:, 7], errors="coerce")
            if raw.shape[1] > 7
            else pd.to_numeric(raw.iloc[:, 5], errors="coerce"),
        }
    )
    df["timestamp"] = pd.to_datetime(df["start_ms"], unit="ms", utc=True)
    return df.set_index("timestamp").sort_index()[COLUMNS]


def ensure_spot_1m_archive(
    *,
    symbol: str,
    start: str,
    end: str,
    cache_dir: str | Path,
    force: bool = False,
) -> pd.DataFrame:
    """1分足を data.binance.vision の月次/日次 zip から取る（API ページングより速い）。"""
    from autotrade.data.binance_derivatives import _daterange, _fetch_many, _monthrange

    cache_dir = Path(cache_dir)
    cache_path = cache_dir / f"{symbol}_binance_spot_1m_{start}_{end}.csv"
    if cache_path.exists() and not force:
        return load_ohlcv(cache_path)

    parts: list[pd.DataFrame] = []
    for month in _monthrange(start, end):
        monthly_url = (
            f"{ARCHIVE_BASE}/spot/monthly/klines/{symbol}/1m/"
            f"{symbol}-1m-{month:%Y-%m}.zip"
        )
        monthly, _ = _fetch_many([monthly_url], workers=4)
        if monthly:
            parts.extend(_klines_zip_to_ohlcv(raw) for raw in monthly)
            continue
        m0 = month if month.tzinfo else month.tz_localize("UTC")
        day_lo = max(pd.Timestamp(start, tz="UTC"), m0)
        day_hi = min(pd.Timestamp(end, tz="UTC"), m0 + pd.offsets.MonthEnd(0))
        urls = [
            f"{ARCHIVE_BASE}/spot/daily/klines/{symbol}/1m/{symbol}-1m-{d:%Y-%m-%d}.zip"
            for d in _daterange(day_lo.strftime("%Y-%m-%d"), day_hi.strftime("%Y-%m-%d"))
        ]
        daily, missing = _fetch_many(urls, workers=8)
        if not daily:
            raise RuntimeError(f"no 1m archive for {symbol} {m0:%Y-%m} (miss {len(missing)})")
        parts.extend(_klines_zip_to_ohlcv(raw) for raw in daily)

    df = pd.concat(parts).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
    df = df.loc[(df.index >= lo) & (df.index <= hi)]
    save_ohlcv(df, cache_path)
    return df
