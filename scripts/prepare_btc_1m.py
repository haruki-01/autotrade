"""直近1年の BTCUSDT 1分足を lock する。

Usage:
    PYTHONPATH=src python3 scripts/prepare_btc_1m.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.data.binance_vision import ensure_spot_1m_archive  # noqa: E402
from autotrade.eval import _git_head, _sha256_file, load_eval_config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v4_btc_1m.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v4_btc_1m.lock.yaml")
    ap.add_argument("--warmup-days", type=int, default=40)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg, policy, raw = load_eval_config(args.config)
    cache_dir = Path("data/cache")
    datasets: dict = {}
    for set_name, window in cfg.sets.items():
        fetch_start = (
            pd.Timestamp(window.start, tz="UTC") - pd.Timedelta(days=args.warmup_days)
        ).strftime("%Y-%m-%d")
        fetch_end = window.end
        print(f"fetch 1m {cfg.symbol} {fetch_start}..{fetch_end}")
        df = ensure_spot_1m_archive(
            symbol=cfg.symbol,
            start=fetch_start,
            end=fetch_end,
            cache_dir=cache_dir,
            force=args.force,
        )
        path = cache_dir / f"{cfg.symbol}_binance_spot_1m_{fetch_start}_{fetch_end}.csv"
        print(f"  bars={len(df):,}  file={path}")
        datasets[set_name] = {
            "eval_window": {"start": window.start, "end": window.end},
            "fetch_window": {"start": fetch_start, "end": fetch_end},
            "symbols": {
                cfg.symbol: {
                    "data_source": "binance_vision",
                    "files": {str(path.as_posix()): _sha256_file(path)},
                }
            },
        }

    lock = {
        "schema_version": 1,
        "eval_version": policy.eval_version,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_head(),
        "config_path": str(Path(args.config).as_posix()),
        "config_sha256": _sha256_file(Path(args.config)),
        "forbid_synthetic": True,
        "symbols": [cfg.symbol],
        "interval": "1m",
        "costs": {
            "fee_rate_per_side": cfg.fee_rate_per_side,
            "slippage_pct_per_side": cfg.slippage_pct_per_side,
        },
        "sizing": {
            "mode": cfg.sizing_mode,
            "margin_per_trade": cfg.margin_per_trade,
            "risk_per_trade_usdt": cfg.risk_per_trade_usdt,
            "leverage": cfg.leverage,
            "initial_equity": cfg.initial_equity,
        },
        "gates": {
            "min_trades": cfg.min_trades,
            "max_drawdown_pct": cfg.max_drawdown_pct,
            "min_trades_per_month": cfg.min_trades_per_month,
        },
        "datasets": datasets,
        "notes": (
            "1m screening lock. Formal 8-year gate remains eval_v3_btc. "
            "Only logics that are profitable on set Y proceed to 8-year eval."
        ),
    }
    lock_path = Path(args.lock)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(yaml.safe_dump(lock, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"wrote {lock_path}")


if __name__ == "__main__":
    main()
