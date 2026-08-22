import pytest

from autotrade.portfolio import Portfolio


def test_buy_spends_all_cash():
    p = Portfolio(cash=1_000.0)
    units = p.buy(100.0)
    assert units == pytest.approx(10.0)
    assert p.cash == 0.0
    assert p.position == pytest.approx(10.0)


def test_sell_liquidates_position():
    p = Portfolio(cash=1_000.0)
    p.buy(100.0)
    proceeds = p.sell(120.0)
    assert proceeds == pytest.approx(1_200.0)
    assert p.position == 0.0
    assert p.cash == pytest.approx(1_200.0)


def test_equity_marks_position_to_price():
    p = Portfolio(cash=1_000.0)
    p.buy(100.0)  # 10 units
    assert p.equity(150.0) == pytest.approx(1_500.0)


def test_buy_with_no_cash_is_noop():
    p = Portfolio(cash=0.0)
    assert p.buy(100.0) == 0.0


def test_invalid_price_raises():
    p = Portfolio(cash=100.0)
    with pytest.raises(ValueError):
        p.buy(0)
