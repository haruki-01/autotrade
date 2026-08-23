"""L-COST — same entries as H01, skip when expected move < round-trip cost buffer."""

from __future__ import annotations

import pandas as pd

from autotrade.strategy.mtf_trend import StrategyParams, prepare_frames as prepare_h01


def prepare_frames(
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    params: StrategyParams,
    *,
    fee_rate: float = 0.00055,
    slippage_pct: float = 0.0002,
    cost_buffer_mult: float = 1.5,
    atr_stop_mult: float = 1.0,
) -> pd.DataFrame:
    merged = prepare_h01(daily, h4, m15, params)
    round_trip = 2.0 * (fee_rate + slippage_pct) * cost_buffer_mult
    atr_pct = (merged["atr"] / merged["close"]).fillna(0.0)
    # Require ATR (proxy for reachable move to stop) to clear cost hurdle
    affordable = atr_pct * atr_stop_mult >= round_trip
    merged["long_signal"] = merged["long_signal"] & affordable
    merged["short_signal"] = merged["short_signal"] & affordable
    merged["cost_gate_pass"] = affordable
    # Keep fixed exits; cost gate only filters entry
    return merged
