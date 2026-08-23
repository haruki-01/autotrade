from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import numpy as np
import pandas as pd


class ExitReason(str, Enum):
    STOP = "stop"
    TAKE_PROFIT = "take_profit"
    TRAIL = "trail"
    H4_BREAK = "h4_break"
    DAILY_BREAK = "daily_break"
    STRUCTURE = "structure"
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
    funding: float = 0.0


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    final_equity: float
    initial_equity: float


def _apply_slippage(price: float, side: str, is_entry: bool, slip: float) -> float:
    if side == "long":
        return price * (1 + slip) if is_entry else price * (1 - slip)
    return price * (1 - slip) if is_entry else price * (1 + slip)


def _row_float(row: pd.Series, key: str, default: float | None = None) -> float | None:
    if key not in row.index:
        return default
    val = row[key]
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return float(val)


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
    sizing_mode: str = "equity_pct",
    margin_per_trade: float = 30.0,
    risk_per_trade_usdt: float = 3.0,
) -> BacktestResult:
    """Event loop on 15m bars. Signal on bar t close → fill at bar t+1 open (+slip).

    sizing_mode:
      - equity_pct: risk = equity * risk_per_trade_pct%; notional cap = equity * lev
      - fixed_margin: risk = risk_per_trade_usdt; notional cap = margin_per_trade * lev
        (demo unit: margin $30 × lev 3 → max notional $90, risk $3)
    """
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

        if pending is not None and position is None:
            fill = _apply_slippage(float(row["open"]), pending["side"], True, slippage_pct)
            stop_pct = pending["stop_pct"] / 100.0
            stop_dist = fill * stop_pct
            if sizing_mode == "fixed_margin":
                risk_cash = risk_per_trade_usdt
                max_notional = margin_per_trade * leverage
            else:
                risk_cash = equity * (risk_per_trade_pct / 100.0)
                max_notional = equity * leverage
            qty = risk_cash / stop_dist if stop_dist > 0 else 0.0
            if qty * fill > max_notional:
                qty = max_notional / fill
            fee = qty * fill * fee_rate
            equity -= fee
            if pending["side"] == "long":
                stop = fill * (1 - stop_pct)
                tp = (
                    None
                    if pending["tp_pct"] is None
                    else fill * (1 + pending["tp_pct"] / 100.0)
                )
            else:
                stop = fill * (1 + stop_pct)
                tp = (
                    None
                    if pending["tp_pct"] is None
                    else fill * (1 - pending["tp_pct"] / 100.0)
                )
            position = {
                "side": pending["side"],
                "entry_time": ts,
                "entry_price": fill,
                "qty": qty,
                "stop": stop,
                "tp": tp,
                "entry_fee": fee,
                "trail_atr_mult": pending.get("trail_atr_mult"),
                "initial_stop": stop,
                "funding_paid": 0.0,
            }
            pending = None

        if position is not None:
            side = position["side"]
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            exit_price = None
            reason = None

            # Perp funding: charged on notional at each settlement bar.
            # Only frames that supply funding_pay_rate are affected.
            rate = _row_float(row, "funding_pay_rate", 0.0)
            if rate:
                cost = position["qty"] * close * rate
                position["funding_paid"] += cost if side == "long" else -cost

            # Trailing stop (ATR) — ratchet only
            trail_mult = position.get("trail_atr_mult")
            atr_val = _row_float(row, "atr")
            if trail_mult is not None and atr_val is not None and atr_val > 0:
                if side == "long":
                    trailed = close - atr_val * trail_mult
                    if trailed > position["stop"]:
                        position["stop"] = trailed
                else:
                    trailed = close + atr_val * trail_mult
                    if trailed < position["stop"]:
                        position["stop"] = trailed

            if side == "long":
                hit_stop = low <= position["stop"]
                hit_tp = position["tp"] is not None and high >= position["tp"]
                struct = bool(row.get("structure_exit_long", False))
                if hit_stop and hit_tp:
                    exit_price = position["stop"]
                    reason = (
                        ExitReason.TRAIL.value
                        if position.get("trail_atr_mult")
                        else ExitReason.STOP.value
                    )
                elif hit_stop:
                    exit_price = position["stop"]
                    reason = (
                        ExitReason.TRAIL.value
                        if position.get("trail_atr_mult")
                        and position["stop"] != position.get("initial_stop")
                        else ExitReason.STOP.value
                    )
                elif hit_tp:
                    exit_price = position["tp"]
                    reason = ExitReason.TAKE_PROFIT.value
                elif struct:
                    exit_price = close
                    reason = ExitReason.STRUCTURE.value
                elif bool(row.get("h4_long_break", False)) or bool(
                    row.get("daily_against_long", False)
                ):
                    exit_price = close
                    reason = (
                        ExitReason.DAILY_BREAK.value
                        if bool(row.get("daily_against_long", False))
                        else ExitReason.H4_BREAK.value
                    )
            else:
                hit_stop = high >= position["stop"]
                hit_tp = position["tp"] is not None and low <= position["tp"]
                struct = bool(row.get("structure_exit_short", False))
                if hit_stop and hit_tp:
                    exit_price = position["stop"]
                    reason = (
                        ExitReason.TRAIL.value
                        if position.get("trail_atr_mult")
                        else ExitReason.STOP.value
                    )
                elif hit_stop:
                    exit_price = position["stop"]
                    reason = (
                        ExitReason.TRAIL.value
                        if position.get("trail_atr_mult")
                        and position["stop"] != position.get("initial_stop")
                        else ExitReason.STOP.value
                    )
                elif hit_tp:
                    exit_price = position["tp"]
                    reason = ExitReason.TAKE_PROFIT.value
                elif struct:
                    exit_price = close
                    reason = ExitReason.STRUCTURE.value
                elif bool(row.get("h4_short_break", False)) or bool(
                    row.get("daily_against_short", False)
                ):
                    exit_price = close
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
                funding_paid = position.get("funding_paid", 0.0)
                pnl = raw - fee - funding_paid
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
                        funding=funding_paid,
                    )
                )
                position = None
                peak = max(peak, equity)

        if position is None and pending is None and i < len(times) - 1:
            stop_pct = _row_float(row, "stop_pct", stop_loss_pct)
            assert stop_pct is not None
            if "tp_pct" in row.index and pd.isna(row["tp_pct"]):
                tp_pct = None
            else:
                tp_pct = _row_float(row, "tp_pct", take_profit_pct)
            trail = _row_float(row, "trail_atr_mult")
            if bool(row.get("long_signal", False)):
                pending = {
                    "side": "long",
                    "stop_pct": stop_pct,
                    "tp_pct": tp_pct,
                    "trail_atr_mult": trail,
                }
            elif bool(row.get("short_signal", False)):
                pending = {
                    "side": "short",
                    "stop_pct": stop_pct,
                    "tp_pct": tp_pct,
                    "trail_atr_mult": trail,
                }

    if position is not None:
        ts = times[-1]
        row = frame.iloc[-1]
        exit_fill = _apply_slippage(float(row["close"]), position["side"], False, slippage_pct)
        fee = position["qty"] * exit_fill * fee_rate
        if position["side"] == "long":
            raw = (exit_fill - position["entry_price"]) * position["qty"]
        else:
            raw = (position["entry_price"] - exit_fill) * position["qty"]
        funding_paid = position.get("funding_paid", 0.0)
        pnl = raw - fee - funding_paid
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
                funding=funding_paid,
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
                "funding",
            ]
        )
    return pd.DataFrame([asdict(t) for t in trades])
