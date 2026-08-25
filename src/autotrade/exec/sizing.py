"""Position size used by the backtest engine and by demo/live.

Keep this identical so a demo fill is the same qty the eval would have used.
"""

from __future__ import annotations

import math


def qty_fixed_margin(
    fill_price: float,
    stop_pct: float,
    *,
    risk_usdt: float = 3.0,
    margin: float = 30.0,
    leverage: float = 3.0,
    qty_step: float = 0.001,
    min_qty: float = 0.001,
) -> float:
    """``stop_pct`` is percent (e.g. 4.0 for 4%), matching the strategy frame."""
    if fill_price <= 0 or stop_pct <= 0:
        return 0.0
    stop_dist = fill_price * (stop_pct / 100.0)
    qty = risk_usdt / stop_dist
    max_notional = margin * leverage
    if qty * fill_price > max_notional:
        qty = max_notional / fill_price
    if qty_step > 0:
        qty = math.floor(qty / qty_step + 1e-12) * qty_step
    if qty < min_qty:
        return 0.0
    return float(qty)


def stop_take_prices(
    side: str, fill: float, stop_pct: float, tp_pct: float | None
) -> tuple[float, float | None]:
    frac = stop_pct / 100.0
    if side == "long":
        stop = fill * (1 - frac)
        tp = None if tp_pct is None else fill * (1 + tp_pct / 100.0)
    else:
        stop = fill * (1 + frac)
        tp = None if tp_pct is None else fill * (1 - tp_pct / 100.0)
    return stop, tp
