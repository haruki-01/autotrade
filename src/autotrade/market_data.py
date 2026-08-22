"""Offline market-data feed.

A real trading bot would stream prices from an exchange (Binance, Coinbase,
etc.). To keep this project fully runnable and testable without network access
or API keys, we generate a deterministic pseudo-random price series using a
simple seeded random walk.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    """A single price observation for a symbol."""

    step: int
    symbol: str
    price: float


def simulated_prices(
    symbol: str = "BTC/USDT",
    *,
    start_price: float = 30_000.0,
    steps: int = 200,
    volatility: float = 0.02,
    seed: int = 42,
) -> Iterator[Candle]:
    """Yield a deterministic random-walk price series.

    The series is reproducible for a given ``seed`` so that tests and demos
    produce stable output.
    """

    if steps <= 0:
        raise ValueError("steps must be positive")
    if start_price <= 0:
        raise ValueError("start_price must be positive")

    rng = random.Random(seed)
    price = start_price
    for step in range(steps):
        shock = rng.uniform(-volatility, volatility)
        price = max(0.01, price * (1.0 + shock))
        yield Candle(step=step, symbol=symbol, price=round(price, 2))
