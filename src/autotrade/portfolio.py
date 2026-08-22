"""Paper-trading portfolio accounting.

Tracks available cash and a single-asset position. Orders are "all-in / all-out"
market orders for simplicity, which is enough to demonstrate the end-to-end flow
of a trading bot without a real exchange.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Portfolio:
    """A simple cash + single-position paper-trading account."""

    cash: float
    position: float = 0.0  # units of the asset currently held

    def __post_init__(self) -> None:
        if self.cash < 0:
            raise ValueError("cash cannot be negative")

    def buy(self, price: float) -> float:
        """Spend all available cash to buy the asset. Returns units bought."""

        if price <= 0:
            raise ValueError("price must be positive")
        if self.cash <= 0:
            return 0.0
        units = self.cash / price
        self.position += units
        self.cash = 0.0
        return units

    def sell(self, price: float) -> float:
        """Sell the entire position. Returns cash proceeds."""

        if price <= 0:
            raise ValueError("price must be positive")
        if self.position <= 0:
            return 0.0
        proceeds = self.position * price
        self.cash += proceeds
        self.position = 0.0
        return proceeds

    def equity(self, price: float) -> float:
        """Total account value (cash + position marked at ``price``)."""

        return self.cash + self.position * price
