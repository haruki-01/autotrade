from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from autotrade.data.bybit import save_ohlcv


def _make_ohlcv(index: pd.DatetimeIndex, close: np.ndarray) -> pd.DataFrame:
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (1 + 0.0008)
    low = np.minimum(open_, close) * (1 - 0.0008)
    vol = np.full(len(close), 100.0)
    df = pd.DataFrame(
        {
            "start_ms": (index.asi8 // 10**6).astype("int64"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
            "turnover": vol * close,
        },
        index=index,
    )
    df.index.name = "timestamp"
    return df


def generate_synthetic_btc(
    start: str = "2023-01-01",
    end: str = "2024-12-31",
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Generate correlated 1d/4h/15m OHLCV for offline smoke tests."""
    rng = np.random.default_rng(seed)
    idx_15 = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    # Geometric brownian-ish with regime drift
    n = len(idx_15)
    drifts = np.zeros(n)
    # alternate bull/bear regimes ~ every ~3 months of 15m bars
    regime_len = int(90 * 24 * 4)
    for i, start_i in enumerate(range(0, n, regime_len)):
        drifts[start_i : start_i + regime_len] = 0.00015 if i % 2 == 0 else -0.00012
    shocks = rng.normal(0, 0.0015, size=n)
    log_ret = drifts + shocks
    close_15 = 30000 * np.exp(np.cumsum(log_ret))
    m15 = _make_ohlcv(idx_15, close_15)

    # Resample to 4h and 1d
    def resample(rule: str) -> pd.DataFrame:
        o = m15["open"].resample(rule).first()
        h = m15["high"].resample(rule).max()
        l = m15["low"].resample(rule).min()
        c = m15["close"].resample(rule).last()
        v = m15["volume"].resample(rule).sum()
        idx = o.dropna().index
        return _make_ohlcv(idx, c.reindex(idx).to_numpy())

    return {"15m": m15, "4h": resample("4h"), "1d": resample("1D")}


def write_synthetic_cache(
    cache_dir: str | Path,
    *,
    symbol: str = "BTCUSDT",
    category: str = "linear",
    start: str,
    end: str,
) -> dict[str, Path]:
    frames = generate_synthetic_btc(start=start, end=end)
    cache_dir = Path(cache_dir)
    paths = {}
    for interval, df in frames.items():
        path = cache_dir / f"{symbol}_{category}_{interval}_{start}_{end}.csv"
        save_ohlcv(df, path)
        paths[interval] = path
    return paths
