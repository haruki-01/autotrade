# AGENTS.md

`autotrade` is a small, self-contained cryptocurrency paper-trading bot written
in Python. See `README.md` for the architecture, commands, and options, and
`pyproject.toml` for dependencies and the `ruff`/`pytest` configuration.

## Cursor Cloud specific instructions

- The base image ships Python 3.12 and system `pip`, but **not** `python3.12-venv`
  (there is no `ensurepip`), so `python3 -m venv` fails on a fresh VM. On the
  Cloud VM, dependencies are therefore installed into the **user site** (not a
  venv) via the startup update script:
  `python3 -m pip install --break-system-packages -e ".[dev]"`.
  The `venv` workflow in `README.md` is for local development only (a human can
  `apt install python3.12-venv` first).
- Console scripts (`autotrade`, `pytest`, `ruff`) are installed to
  `~/.local/bin`, which is on `PATH` in login shells. If a non-login shell can't
  find them, use the PATH-independent forms: `python3 -m pytest`,
  `python3 -m ruff check .`, `python3 -m autotrade.cli`.
- Commands (details in `README.md`): lint `ruff check .`, test `pytest`, run
  `autotrade --symbol BTC/USDT --cash 1000`.
- The app is fully **offline**: the market feed is a deterministic simulated
  random walk (`autotrade.market_data`), so no exchange account, API keys, or
  network access are required to run or test it. Runs are reproducible for a
  given `--seed`.
