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
