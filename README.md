# autotrade

仮想通貨の自動取引bot (a cryptocurrency automated trading bot).

This repository contains a small, self-contained **paper-trading** engine that
demonstrates the full flow of an automated trading bot without needing a real
exchange account or API keys:

1. `autotrade.market_data` — generates an offline, deterministic price feed.
2. `autotrade.strategy` — an SMA-crossover strategy that emits BUY/SELL/HOLD.
3. `autotrade.portfolio` — cash + position accounting for paper trades.
4. `autotrade.bot` — wires the feed, strategy and portfolio into a session.
5. `autotrade.cli` — a command-line entry point.

## Requirements

- Python 3.10+

## Setup (development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the app

Run a paper-trading session against the built-in simulated market feed:

```bash
autotrade --symbol BTC/USDT --cash 1000
# or, without activating the venv:
.venv/bin/autotrade --symbol BTC/USDT --cash 1000
# or as a module:
python -m autotrade.cli --symbol BTC/USDT --cash 1000
```

Useful options: `--steps`, `--seed`, `--short-window`, `--long-window`.

## Lint

```bash
ruff check .
```

## Test

```bash
pytest
```

## Project layout

```
src/autotrade/     # library + CLI
tests/             # pytest suite
pyproject.toml     # packaging, dependencies, ruff & pytest config
```
