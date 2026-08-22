"""Command-line entry point for the autotrade bot."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from autotrade.bot import TradingBot
from autotrade.strategy import SmaCrossStrategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autotrade",
        description="Run a paper-trading session for a crypto trading strategy.",
    )
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair symbol.")
    parser.add_argument("--cash", type=float, default=1_000.0, help="Starting cash.")
    parser.add_argument("--steps", type=int, default=200, help="Number of price steps.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for the feed.")
    parser.add_argument("--short-window", type=int, default=5, help="Short SMA window.")
    parser.add_argument("--long-window", type=int, default=20, help="Long SMA window.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    strategy = SmaCrossStrategy(
        short_window=args.short_window,
        long_window=args.long_window,
    )
    bot = TradingBot(strategy=strategy, starting_cash=args.cash)
    result = bot.run_simulation(args.symbol, steps=args.steps, seed=args.seed)

    print(f"=== autotrade paper-trading session: {result.symbol} ===")
    print(f"starting cash : {result.starting_cash:,.2f}")
    print(f"strategy      : SMA cross ({args.short_window}/{args.long_window})")
    print(f"price steps   : {args.steps} (seed={args.seed})")
    print("-" * 48)

    if result.trades:
        for trade in result.trades:
            print(
                f"step {trade.step:>4}  {trade.action.value:<4}  "
                f"price={trade.price:>12,.2f}  units={trade.units:>10.6f}  "
                f"equity={trade.equity:>12,.2f}"
            )
    else:
        print("no trades were triggered by the strategy")

    print("-" * 48)
    print(f"trades        : {len(result.trades)}")
    print(f"final equity  : {result.final_equity:,.2f}")
    print(f"pnl           : {result.pnl:,.2f} ({result.return_pct:+.2f}%)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
