from __future__ import annotations

import hmac
import hashlib

import pandas as pd

from autotrade.exec.bybit_private import sign
from autotrade.exec.secrets import BybitCreds, assert_demo_only
from autotrade.exec.signals import intent_for_bar, last_complete_bar
from autotrade.exec.sizing import qty_fixed_margin, stop_take_prices


def test_qty_matches_eval_formula():
    fill = 60_000.0
    stop_pct = 4.0  # 4% stop → $2400 distance
    qty = qty_fixed_margin(fill, stop_pct, risk_usdt=3.0, margin=30.0, leverage=3.0, qty_step=0.001)
    # risk 3 / 2400 = 0.00125 → floor to 0.001, notional 60 < 90 cap
    assert qty == 0.001


def test_stop_prices_long_short():
    sl, tp = stop_take_prices("long", 100.0, 2.0, 4.0)
    assert abs(sl - 98.0) < 1e-9
    assert abs(tp - 104.0) < 1e-9
    sl, tp = stop_take_prices("short", 100.0, 2.0, None)
    assert abs(sl - 102.0) < 1e-9
    assert tp is None


def test_last_complete_bar_drops_in_progress():
    idx = pd.date_range("2026-08-25 00:00", periods=3, freq="15min", tz="UTC")
    df = pd.DataFrame({"close": [1.0, 2.0, 3.0], "open": 1.0, "high": 1.0, "low": 1.0}, index=idx)
    now = pd.Timestamp("2026-08-25 00:32", tz="UTC")  # last bar 00:30 still open until 00:45
    row = last_complete_bar(df, now)
    assert row.name == idx[1]
    assert float(row["close"]) == 2.0
    now2 = pd.Timestamp("2026-08-25 00:45", tz="UTC")
    row2 = last_complete_bar(df, now2)
    assert float(row2["close"]) == 3.0


def test_intent_enter_then_structure_exit():
    row = pd.Series(
        {
            "close": 100.0,
            "stop_pct": 3.0,
            "tp_pct": 12.0,
            "long_signal": True,
            "short_signal": False,
            "structure_exit_long": False,
            "structure_exit_short": False,
        },
        name=pd.Timestamp("2026-01-01", tz="UTC"),
    )
    enter = intent_for_bar("sh01n_regime_100d", row, position_side=None)
    assert enter.action == "enter_long"
    held = intent_for_bar("sh01n_regime_100d", row, position_side="long")
    assert held.action == "flat"
    row2 = row.copy()
    row2["long_signal"] = False
    row2["structure_exit_long"] = True
    ex = intent_for_bar("sh01n_regime_100d", row2, position_side="long")
    assert ex.action == "exit_long"


def test_hmac_sign_stable():
    got = sign("secret", "123key5000{}")
    expect = hmac.new(b"secret", b"123key5000{}", hashlib.sha256).hexdigest()
    assert got == expect


def test_assert_demo_rejects_mainnet():
    creds = BybitCreds(
        env="demo",
        api_key="x",
        api_secret="y",
        base_url="https://api.bybit.com",
        path=__file__,
    )
    try:
        assert_demo_only(creds)
        raise AssertionError("should refuse mainnet")
    except SystemExit:
        pass


def test_assert_demo_accepts_testnet():
    creds = BybitCreds(
        env="demo",
        api_key="x",
        api_secret="y",
        base_url="https://api-testnet.bybit.com",
        path=__file__,
    )
    assert_demo_only(creds)
