from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import pandas as pd


class ExitReason(str, Enum):
    STOP = "stop"
    TAKE_PROFIT = "take_profit"
    H4_BREAK = "h4_break"
    DAILY_BREAK = "daily_break"
    END = "end"


@dataclass
class Trade:
    side: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    fee: float
    reason: str
    return_pct: float


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    final_equity: float
    initial_equity: float


def _apply_slippage(price: float, side: str, is_entry: bool, slip: float) -> float:
    # Buy pays more, sell receives less
    if side == "long":
        return price * (1 + slip) if is_entry else price * (1 - slip)
    return price * (1 - slip) if is_entry else price * (1 + slip)


def run_backtest(
    frame: pd.DataFrame,
    *,
    initial_equity: float,
    leverage: float,
    risk_per_trade_pct: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    fee_rate: float,
    slippage_pct: float,
) -> BacktestResult:
    """Event loop on 15m bars. Signal on bar t close → fill at bar t+1 open (+slip)."""
    equity = initial_equity
    peak = equity
    equities: list[tuple[pd.Timestamp, float]] = []
    trades: list[Trade] = []

    position: dict | None = None
    pending: dict | None = None

    times = list(frame.index)
    for i, ts in enumerate(times):
        row = frame.iloc[i]
        equities.append((ts, equity))

        # Fill pending entry at this bar open
        if pending is not None and position is None:
            fill = _apply_slippage(float(row["open"]), pending["side"], True, slippage_pct)
            stop_pct = stop_loss_pct / 100.0
            risk_cash = equity * (risk_per_trade_pct / 100.0)
            # qty such that stop distance * qty ~= risk_cash; notional capped by leverage
            stop_dist = fill * stop_pct
            qty = risk_cash / stop_dist if stop_dist > 0 else 0.0
            max_notional = equity * leverage
            if qty * fill > max_notional:
                qty = max_notional / fill
            fee = qty * fill * fee_rate
            equity -= fee
            if pending["side"] == "long":
                stop = fill * (1 - stop_pct)
                tp = fill * (1 + take_profit_pct / 100.0)
            else:
                stop = fill * (1 + stop_pct)
                tp = fill * (1 - take_profit_pct / 100.0)
            position = {
                "side": pending["side"],
                "entry_time": ts,
                "entry_price": fill,
                "qty": qty,
                "stop": stop,
                "tp": tp,
                "entry_fee": fee,
            }
            pending = None

        # Manage open position using this bar's OHLC (conservative: stop before tp if both)
        if position is not None:
            side = position["side"]
            high = float(row["high"])
            low = float(row["low"])
            exit_price = None
            reason = None

            if side == "long":
                hit_stop = low <= position["stop"]
                hit_tp = high >= position["tp"]
                if hit_stop and hit_tp:
                    exit_price = position["stop"]
                    reason = ExitReason.STOP.value
                elif hit_stop:
                    exit_price = position["stop"]
                    reason = ExitReason.STOP.value
                elif hit_tp:
                    exit_price = position["tp"]
                    reason = ExitReason.TAKE_PROFIT.value
                elif bool(row.get("h4_long_break", False)) or bool(row.get("daily_against_long", False)):
                    exit_price = float(row["close"])
                    reason = (
                        ExitReason.DAILY_BREAK.value
                        if bool(row.get("daily_against_long", False))
                        else ExitReason.H4_BREAK.value
                    )
            else:
                hit_stop = high >= position["stop"]
                hit_tp = low <= position["tp"]
                if hit_stop and hit_tp:
                    exit_price = position["stop"]
                    reason = ExitReason.STOP.value
                elif hit_stop:
                    exit_price = position["stop"]
                    reason = ExitReason.STOP.value
                elif hit_tp:
                    exit_price = position["tp"]
                    reason = ExitReason.TAKE_PROFIT.value
                elif bool(row.get("h4_short_break", False)) or bool(row.get("daily_against_short", False)):
                    exit_price = float(row["close"])
                    reason = (
                        ExitReason.DAILY_BREAK.value
                        if bool(row.get("daily_against_short", False))
                        else ExitReason.H4_BREAK.value
                    )

            if exit_price is not None and reason is not None:
                exit_fill = _apply_slippage(exit_price, side, False, slippage_pct)
                fee = position["qty"] * exit_fill * fee_rate
                if side == "long":
                    raw = (exit_fill - position["entry_price"]) * position["qty"]
                else:
                    raw = (position["entry_price"] - exit_fill) * position["qty"]
                pnl = raw - fee
                equity += pnl
                ret = pnl / initial_equity * 100.0
                trades.append(
                    Trade(
                        side=side,
                        entry_time=position["entry_time"],
                        exit_time=ts,
                        entry_price=position["entry_price"],
                        exit_price=exit_fill,
                        qty=position["qty"],
                        pnl=pnl,
                        fee=position["entry_fee"] + fee,
                        reason=reason,
                        return_pct=ret,
                    )
                )
                position = None
                peak = max(peak, equity)

        # Queue new signal only if flat and no pending (use confirmed bar signal → next open)
        if position is None and pending is None and i < len(times) - 1:
            if bool(row["long_signal"]):
                pending = {"side": "long"}
            elif bool(row["short_signal"]):
                pending = {"side": "short"}

    # Force close at end
    if position is not None:
        ts = times[-1]
        row = frame.iloc[-1]
        exit_fill = _apply_slippage(float(row["close"]), position["side"], False, slippage_pct)
        fee = position["qty"] * exit_fill * fee_rate
        if position["side"] == "long":
            raw = (exit_fill - position["entry_price"]) * position["qty"]
        else:
            raw = (position["entry_price"] - exit_fill) * position["qty"]
        pnl = raw - fee
        equity += pnl
        trades.append(
            Trade(
                side=position["side"],
                entry_time=position["entry_time"],
                exit_time=ts,
                entry_price=position["entry_price"],
                exit_price=exit_fill,
                qty=position["qty"],
                pnl=pnl,
                fee=position["entry_fee"] + fee,
                reason=ExitReason.END.value,
                return_pct=pnl / initial_equity * 100.0,
            )
        )

    curve = pd.Series({t: e for t, e in equities}, name="equity").sort_index()
    return BacktestResult(
        trades=trades,
        equity_curve=curve,
        final_equity=equity,
        initial_equity=initial_equity,
    )


def trades_to_frame(trades: list[Trade]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame(
            columns=[
                "side",
                "entry_time",
                "exit_time",
                "entry_price",
                "exit_price",
                "qty",
                "pnl",
                "fee",
                "reason",
                "return_pct",
            ]
        )
    return pd.DataFrame([asdict(t) for t in trades])
