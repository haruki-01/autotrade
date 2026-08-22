from autotrade.bot import TradingBot
from autotrade.market_data import simulated_prices


def test_simulated_feed_is_deterministic():
    a = [c.price for c in simulated_prices(steps=50, seed=7)]
    b = [c.price for c in simulated_prices(steps=50, seed=7)]
    assert a == b
    assert len(a) == 50


def test_bot_runs_and_reports_result():
    bot = TradingBot(starting_cash=1_000.0)
    result = bot.run_simulation("BTC/USDT", steps=200, seed=42)

    assert result.symbol == "BTC/USDT"
    assert result.starting_cash == 1_000.0
    assert result.final_equity > 0
    # PnL and return are consistent with each other.
    assert result.return_pct == (result.pnl / result.starting_cash * 100.0)


def test_bot_is_reproducible():
    r1 = TradingBot().run_simulation(steps=200, seed=42)
    r2 = TradingBot().run_simulation(steps=200, seed=42)
    assert r1.final_equity == r2.final_equity
    assert len(r1.trades) == len(r2.trades)
