"""Trading strategies.

The bundled strategy is a classic simple-moving-average (SMA) crossover: when
the short-window average crosses above the long-window average it emits a BUY
signal, and when it crosses below it emits a SELL signal.
"""

from __future__ import annotations

from collections import deque
from enum import Enum


class Signal(str, Enum):
    """A trading decision for a single price observation."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SmaCrossStrategy:
    """Simple moving-average crossover strategy.

    Feed prices in chronological order via :meth:`update`; it returns a
    :class:`Signal` for each price once enough history is available.
    """

    def __init__(self, short_window: int = 5, long_window: int = 20) -> None:
        if short_window < 1 or long_window < 1:
            raise ValueError("windows must be positive")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.short_window = short_window
        self.long_window = long_window
        self._prices: deque[float] = deque(maxlen=long_window)
        self._prev_short_above: bool | None = None

    @staticmethod
    def _average(values: list[float]) -> float:
        return sum(values) / len(values)

    def update(self, price: float) -> Signal:
        """Record a new price and return the resulting signal."""

        self._prices.append(price)
        if len(self._prices) < self.long_window:
            return Signal.HOLD

        prices = list(self._prices)
        short_avg = self._average(prices[-self.short_window :])
        long_avg = self._average(prices)
        short_above = short_avg > long_avg

        signal = Signal.HOLD
        if self._prev_short_above is not None and short_above != self._prev_short_above:
            signal = Signal.BUY if short_above else Signal.SELL

        self._prev_short_above = short_above
        return signal
