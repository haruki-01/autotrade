"""The trading engine that ties the pieces together."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from autotrade.market_data import Candle, simulated_prices
from autotrade.portfolio import Portfolio
from autotrade.strategy import Signal, SmaCrossStrategy


@dataclass(frozen=True)
class TradeRecord:
    """A single executed paper trade."""

    step: int
    action: Signal
    price: float
    units: float
    equity: float


@dataclass(frozen=True)
class SessionResult:
    """Summary of a completed trading session."""

    symbol: str
    starting_cash: float
    final_equity: float
    trades: list[TradeRecord]

    @property
    def pnl(self) -> float:
        return self.final_equity - self.starting_cash

    @property
    def return_pct(self) -> float:
        if self.starting_cash == 0:
            return 0.0
        return self.pnl / self.starting_cash * 100.0


class TradingBot:
    """Runs a strategy against a price feed using a paper-trading portfolio."""

    def __init__(
        self,
        strategy: SmaCrossStrategy | None = None,
        starting_cash: float = 1_000.0,
    ) -> None:
        self.strategy = strategy or SmaCrossStrategy()
        self.starting_cash = starting_cash

    def run(self, candles: Iterable[Candle]) -> SessionResult:
        """Execute the strategy over ``candles`` and return the result."""

        portfolio = Portfolio(cash=self.starting_cash)
        trades: list[TradeRecord] = []
        symbol = ""
        last_price = 0.0

        for candle in candles:
            symbol = candle.symbol
            last_price = candle.price
            signal = self.strategy.update(candle.price)

            if signal is Signal.BUY and portfolio.cash > 0:
                units = portfolio.buy(candle.price)
                trades.append(
                    TradeRecord(candle.step, Signal.BUY, candle.price, units,
                                portfolio.equity(candle.price))
                )
            elif signal is Signal.SELL and portfolio.position > 0:
                units = portfolio.position
                portfolio.sell(candle.price)
                trades.append(
                    TradeRecord(candle.step, Signal.SELL, candle.price, units,
                                portfolio.equity(candle.price))
                )

        return SessionResult(
            symbol=symbol,
            starting_cash=self.starting_cash,
            final_equity=portfolio.equity(last_price),
            trades=trades,
        )

    def run_simulation(
        self,
        symbol: str = "BTC/USDT",
        *,
        steps: int = 200,
        seed: int = 42,
    ) -> SessionResult:
        """Convenience helper: run against the built-in simulated feed."""

        candles = simulated_prices(symbol, steps=steps, seed=seed)
        return self.run(candles)
