"""autotrade: a minimal cryptocurrency automated trading bot.

This package provides a small, self-contained paper-trading engine:

- :mod:`autotrade.market_data` generates an offline (simulated) price feed.
- :mod:`autotrade.strategy` turns prices into BUY/SELL/HOLD signals.
- :mod:`autotrade.portfolio` tracks cash, position and equity.
- :mod:`autotrade.bot` wires everything together into a runnable session.
"""

__version__ = "0.1.0"

from autotrade.bot import TradeRecord, TradingBot
from autotrade.portfolio import Portfolio
from autotrade.strategy import Signal, SmaCrossStrategy

__all__ = [
    "TradingBot",
    "TradeRecord",
    "Portfolio",
    "Signal",
    "SmaCrossStrategy",
    "__version__",
]
