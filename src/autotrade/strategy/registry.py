"""Strategy registry — logic_id → prepare_frames."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from autotrade.strategy import (
    cost_gate,
    donchian,
    double_bottom,
    fake_rebreak,
    mom_vol,
    mtf_trend,
    near_high_expanded,
)
from autotrade.strategy.donchian import DonchianParams
from autotrade.strategy.double_bottom import CYCLE_DB, prepare_cycle_db
from autotrade.strategy.h4_spots import CYCLE_LOGICS, prepare_cycle_logic
from autotrade.strategy.mom_vol import MomVolParams
from autotrade.strategy.mtf_trend import StrategyParams

PrepareFn = Callable[..., pd.DataFrame]

LOGIC_META: dict[str, dict[str, Any]] = {
    "mtf_ema_pullback_v1": {
        "hypothesis_id": "H01",
        "name": "MTF EMA押し目 v1",
        "distortion_ids": [],
    },
    "cost_gate_v1": {
        "hypothesis_id": "L-COST",
        "name": "費用ゲート",
        "distortion_ids": ["E8"],
    },
    "vol_scaled_trend_v1": {
        "hypothesis_id": "L-MOM-VOL",
        "name": "ボラ調整トレンド・トレール",
        "distortion_ids": ["E1", "E6"],
    },
    "donchian_20_10_v1": {
        "hypothesis_id": "L-BREAK",
        "name": "Donchian 20/10 ブレイク",
        "distortion_ids": ["E1"],
    },
    "donchian_h4_20_10_v1": {
        "hypothesis_id": "L-BREAK-2",
        "name": "Donchian 20/10 on 4H（サンプル確保）",
        "distortion_ids": ["E1"],
    },
    "donchian_20_10_long_only": {
        "hypothesis_id": "H21",
        "name": "Donchian 20/10 Long only",
        "distortion_ids": ["E1"],
    },
    "donchian_20_10_long_v2": {
        "hypothesis_id": "HYP-002",
        "name": "Donchian Long v2 (新規上抜け+4H確認)",
        "distortion_ids": ["E1"],
    },
    "fake_then_rebreak_v1": {
        "hypothesis_id": "HYP-009",
        "name": "D-001 だまし後本突破初日",
        "distortion_ids": ["E1", "E6", "E8"],
    },
    "fake_then_retest_v1": {
        "hypothesis_id": "HYP-010",
        "name": "D-001 だまし後本突破の再テスト",
        "distortion_ids": ["E1", "E6", "E8"],
    },
    "near_high_expanded_v1": {
        "hypothesis_id": "HYP-011",
        "name": "R-001 高値圏×ボラ拡大",
        "distortion_ids": ["E1", "E6"],
    },
}

for _lid, (_params, _hid, _name) in CYCLE_DB.items():
    LOGIC_META[_lid] = {
        "hypothesis_id": _hid,
        "name": _name,
        "distortion_ids": ["E1"],
        "spot": "SPOT-001",
        "cycle_pack": "double_bottom_20",
    }

for _lid, (_fam, _rule, _hid, _name) in CYCLE_LOGICS.items():
    LOGIC_META[_lid] = {
        "hypothesis_id": _hid,
        "name": _name,
        "distortion_ids": ["E1"],
        "cycle_pack": True,
    }


def prepare_strategy(
    logic_id: str,
    daily: pd.DataFrame,
    h4: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    cfg: Any,
) -> pd.DataFrame:
    base = StrategyParams(
        daily_ema=cfg.daily_ema,
        h4_ema=cfg.h4_ema,
        m15_ema=cfg.m15_ema,
        stop_loss_pct=cfg.stop_loss_pct,
        take_profit_pct=cfg.take_profit_pct,
    )
    if logic_id == "mtf_ema_pullback_v1":
        return mtf_trend.prepare_frames(daily, h4, m15, base)
    if logic_id == "cost_gate_v1":
        return cost_gate.prepare_frames(
            daily,
            h4,
            m15,
            base,
            fee_rate=cfg.fee_rate_per_side,
            slippage_pct=cfg.slippage_pct_per_side,
        )
    if logic_id == "vol_scaled_trend_v1":
        return mom_vol.prepare_frames(daily, h4, m15, MomVolParams())
    if logic_id == "donchian_20_10_v1":
        return donchian.prepare_frames(daily, h4, m15, DonchianParams(long_only=False))
    if logic_id == "donchian_h4_20_10_v1":
        return donchian.prepare_frames(
            daily,
            h4,
            m15,
            DonchianParams(long_only=False, signal_timeframe="h4"),
        )
    if logic_id == "donchian_20_10_long_only":
        return donchian.prepare_frames(daily, h4, m15, DonchianParams(long_only=True))
    if logic_id == "donchian_20_10_long_v2":
        return donchian.prepare_frames(
            daily,
            h4,
            m15,
            DonchianParams(
                long_only=True,
                new_break_only=True,
                require_h4_confirm=True,
            ),
        )
    if logic_id == "fake_then_rebreak_v1":
        return fake_rebreak.prepare_frames_rebreak(daily, h4, m15)
    if logic_id == "fake_then_retest_v1":
        return fake_rebreak.prepare_frames_retest(daily, h4, m15)
    if logic_id == "near_high_expanded_v1":
        return near_high_expanded.prepare_frames(daily, h4, m15)
    if logic_id in CYCLE_DB:
        return prepare_cycle_db(logic_id, daily, h4, m15)
    if logic_id in CYCLE_LOGICS:
        return prepare_cycle_logic(logic_id, daily, h4, m15)
    raise ValueError(f"Unknown logic_id: {logic_id}")


def known_logic_ids() -> list[str]:
    return list(LOGIC_META.keys())
