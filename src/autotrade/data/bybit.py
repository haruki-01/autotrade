from __future__ import annotations

import time
from pathlib import Path

import httpx
import pandas as pd

# Bybit interval codes
INTERVAL_MAP = {
    "1m": "1",
    "15m": "15",
    "4h": "240",
    "1d": "D",
}

COLUMNS = ["start_ms", "open", "high", "low", "close", "volume", "turnover"]


class BybitPublicClient:
    def __init__(self, base_url: str = "https://api.bybit.com", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        *,
        category: str = "linear",
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch all klines between start_ms and end_ms (inclusive bounds via paging)."""
        bybit_interval = INTERVAL_MAP.get(interval, interval)
        rows: list[list[str]] = []
        cursor_end = end_ms

        with httpx.Client(timeout=self.timeout) as client:
            while True:
                params: dict[str, str | int] = {
                    "category": category,
                    "symbol": symbol,
                    "interval": bybit_interval,
                    "limit": limit,
                }
                if start_ms is not None:
                    params["start"] = start_ms
                if cursor_end is not None:
                    params["end"] = cursor_end

                resp = client.get(f"{self.base_url}/v5/market/kline", params=params)
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("retCode") != 0:
                    raise RuntimeError(f"Bybit error: {payload}")

                batch = payload["result"]["list"]
                if not batch:
                    break

                rows.extend(batch)
                oldest = int(batch[-1][0])
                if start_ms is not None and oldest <= start_ms:
                    break
                if len(batch) < limit:
                    break

                # Page older: next end is just before oldest candle
                cursor_end = oldest - 1
                time.sleep(0.05)

        if not rows:
            return pd.DataFrame(columns=COLUMNS)

        df = pd.DataFrame(rows, columns=COLUMNS)
        for col in COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.drop_duplicates(subset=["start_ms"]).sort_values("start_ms")
        df["timestamp"] = pd.to_datetime(df["start_ms"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        if start_ms is not None:
            df = df[df["start_ms"] >= start_ms]
        if end_ms is not None:
            df = df[df["start_ms"] <= end_ms]
        return df


def save_ohlcv(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.reset_index()
    out.to_csv(path, index=False)


def load_ohlcv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
    return df.set_index("timestamp").sort_index()


def ensure_data(
    client: BybitPublicClient,
    *,
    symbol: str,
    category: str,
    interval: str,
    start: str,
    end: str,
    cache_dir: str | Path,
    force: bool = False,
) -> pd.DataFrame:
    """Download (or load cache) OHLCV for [start, end] calendar dates UTC."""
    cache_dir = Path(cache_dir)
    cache_path = cache_dir / f"{symbol}_{category}_{interval}_{start}_{end}.csv"
    if cache_path.exists() and not force:
        return load_ohlcv(cache_path)

    start_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    # end date inclusive through end-of-day
    end_ms = int((pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)).timestamp() * 1000)

    df = client.fetch_klines(
        symbol,
        interval,
        category=category,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    save_ohlcv(df, cache_path)
    return df
