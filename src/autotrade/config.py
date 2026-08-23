from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

SizingMode = Literal["equity_pct", "fixed_margin"]


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
    # Demo / live unit sizing (interpretation B: margin × lev, absolute risk)
    sizing_mode: SizingMode = "equity_pct"
    margin_per_trade: float = 30.0
    risk_per_trade_usdt: float = 3.0

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BacktestConfig":
        sets = {
            name: DateRange(start=v["start"], end=v["end"])
            for name, v in data["sets"].items()
        }
        sizing = data.get("sizing") or {}
        mode = str(sizing.get("mode", data.get("sizing_mode", "equity_pct")))
        if mode not in ("equity_pct", "fixed_margin"):
            mode = "equity_pct"
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
            sizing_mode=mode,  # type: ignore[arg-type]
            margin_per_trade=float(
                sizing.get("margin_per_trade", data.get("margin_per_trade", 30.0))
            ),
            risk_per_trade_usdt=float(
                sizing.get(
                    "risk_per_trade_usdt", data.get("risk_per_trade_usdt", 3.0)
                )
            ),
        )


def load_config(path: str | Path) -> BacktestConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return BacktestConfig.from_dict(raw)
