"""Download OHLCV and derivative caches for every symbol in an eval config.

Separate from lock building so the (slow) network work can run unattended
while the strategy code is written.

Usage:
    python scripts/prewarm_multi_cache.py --config configs/eval_v2.yaml
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml  # noqa: E402

from autotrade.data.binance_derivatives import (  # noqa: E402
    KINDS as DERIV_KINDS,
    ensure_derivative,
)
from autotrade.data.binance_vision import (  # noqa: E402
    BinanceVisionClient,
    ensure_binance_data,
)
from autotrade.eval import _set_bounds, load_eval_config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v2.yaml")
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--cache-dir", default="data/cache")
    ap.add_argument("--skip-derivatives", action="store_true")
    ap.add_argument("--symbols", default="", help="Comma-separated subset; default: all in config")
    args = ap.parse_args()

    cfg, _, raw = load_eval_config(args.config)
    symbols = (
        [s.strip() for s in args.symbols.split(",") if s.strip()]
        or list(raw.get("symbols") or [cfg.symbol])
    )
    sets = [s.strip() for s in args.sets.split(",") if s.strip()]
    cache_dir = Path(args.cache_dir)
    vision = BinanceVisionClient()

    total = len(symbols) * len(sets)
    done = 0
    for symbol in symbols:
        for set_name in sets:
            done += 1
            start, end = _set_bounds(cfg, set_name)
            print(f"[{done}/{total}] {symbol} set={set_name} {start}..{end}", flush=True)
            for interval in ("1d", "4h", "15m"):
                df = ensure_binance_data(
                    vision,
                    symbol=symbol,
                    interval=interval,
                    start=start,
                    end=end,
                    cache_dir=cache_dir,
                )
                print(f"    ohlcv {interval}: {len(df)} bars", flush=True)
            if args.skip_derivatives:
                continue
            for kind in DERIV_KINDS:
                try:
                    ensure_derivative(
                        symbol=symbol, kind=kind, start=start, end=end, cache_dir=cache_dir
                    )
                    print(f"    deriv {kind}: ok", flush=True)
                except Exception:  # noqa: BLE001
                    print(f"    deriv {kind}: FAILED", flush=True)
                    traceback.print_exc()

    print("done", flush=True)


if __name__ == "__main__":
    main()
