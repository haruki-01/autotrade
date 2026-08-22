import pytest

from autotrade.strategy import Signal, SmaCrossStrategy


def test_holds_until_enough_history():
    strat = SmaCrossStrategy(short_window=2, long_window=4)
    assert strat.update(10) is Signal.HOLD
    assert strat.update(11) is Signal.HOLD
    assert strat.update(12) is Signal.HOLD  # still < long_window observations


def test_buy_signal_on_upward_cross():
    strat = SmaCrossStrategy(short_window=2, long_window=4)
    # Prime with a downtrend so short SMA sits below long SMA.
    for price in [40, 30, 20, 10]:
        strat.update(price)
    # Sharp rally pushes the short SMA above the long SMA -> BUY.
    signals = [strat.update(p) for p in [60, 90]]
    assert Signal.BUY in signals


def test_sell_signal_on_downward_cross():
    strat = SmaCrossStrategy(short_window=2, long_window=4)
    for price in [10, 20, 30, 40, 60, 90]:
        strat.update(price)  # establish short-above-long
    signals = [strat.update(p) for p in [5, 1]]
    assert Signal.SELL in signals


def test_invalid_windows():
    with pytest.raises(ValueError):
        SmaCrossStrategy(short_window=5, long_window=5)
    with pytest.raises(ValueError):
        SmaCrossStrategy(short_window=0, long_window=4)
