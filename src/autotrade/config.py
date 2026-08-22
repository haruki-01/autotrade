from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DateRange:
    start: str
    end: str


@dataclass(frozen=True)
class BacktestConfig:
    symbol: str
    category: str
    base_url: str
    initial_equity: float
    leverage: float
    risk_per_trade_pct: float
    daily_ema: int
    h4_ema: int
    m15_ema: int
    stop_loss_pct: float
    take_profit_pct: float
    fee_rate_per_side: float
    slippage_pct_per_side: float
    sets: dict[str, DateRange]
    min_trades: int
    max_drawdown_pct: float

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BacktestConfig":
        sets = {
            name: DateRange(start=v["start"], end=v["end"])
            for name, v in data["sets"].items()
        }
        return BacktestConfig(
            symbol=data["symbol"],
            category=data["category"],
            base_url=data["base_url"],
            initial_equity=float(data["initial_equity"]),
            leverage=float(data["leverage"]),
            risk_per_trade_pct=float(data["risk_per_trade_pct"]),
            daily_ema=int(data["daily_ema"]),
            h4_ema=int(data["h4_ema"]),
            m15_ema=int(data["m15_ema"]),
            stop_loss_pct=float(data["stop_loss_pct"]),
            take_profit_pct=float(data["take_profit_pct"]),
            fee_rate_per_side=float(data["fee_rate_per_side"]),
            slippage_pct_per_side=float(data["slippage_pct_per_side"]),
            sets=sets,
            min_trades=int(data["min_trades"]),
            max_drawdown_pct=float(data["max_drawdown_pct"]),
        )


def load_config(path: str | Path) -> BacktestConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return BacktestConfig.from_dict(raw)
