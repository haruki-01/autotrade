from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from autotrade.config import load_config
from autotrade.data.bybit import BybitPublicClient, ensure_data, load_ohlcv
from autotrade.data.binance_vision import BinanceVisionClient, ensure_binance_data
from autotrade.data.synthetic import write_synthetic_cache
from autotrade.backtest.engine import run_backtest, trades_to_frame
from autotrade.backtest.metrics import compute_metrics, metrics_to_dict, monthly_returns
from autotrade.strategy.mtf_trend import StrategyParams, prepare_frames


def _load_or_fetch_frames(
    cfg, set_name: str, *, force: bool, synthetic: bool
) -> tuple[dict, str]:
    """Return (frames, data_source). source is synthetic|bybit|binance_vision."""
    start, end = _set_bounds(cfg, set_name)
    cache = Path("data/cache")
    frames: dict = {}
    if synthetic:
        write_synthetic_cache(
            cache,
            symbol=cfg.symbol,
            category=cfg.category,
            start=start,
            end=end,
        )
        for interval in ("1d", "4h", "15m"):
            path = cache / f"{cfg.symbol}_{cfg.category}_{interval}_{start}_{end}.csv"
            frames[interval] = load_ohlcv(path)
        return frames, "synthetic"

    # Prefer Bybit (target venue). Fall back to Binance Vision when geo-blocked.
    bybit_client = BybitPublicClient(base_url=cfg.base_url)
    try:
        for interval in ("1d", "4h", "15m"):
            frames[interval] = ensure_data(
                bybit_client,
                symbol=cfg.symbol,
                category=cfg.category,
                interval=interval,
                start=start,
                end=end,
                cache_dir=cache,
                force=force,
            )
        return frames, "bybit"
    except Exception as bybit_exc:  # noqa: BLE001
        print(
            f"Bybit fetch failed ({bybit_exc}).\n"
            "Falling back to Binance Vision public BTCUSDT klines for research.\n"
            "Note: not identical to Bybit linear; re-run on Bybit locally before live.",
            file=sys.stderr,
        )

    vision = BinanceVisionClient()
    for interval in ("1d", "4h", "15m"):
        frames[interval] = ensure_binance_data(
            vision,
            symbol=cfg.symbol,
            interval=interval,
            start=start,
            end=end,
            cache_dir=cache,
            force=force,
        )
    return frames, "binance_vision"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="autotrade CLI")
    sub = p.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch-data", help="Download Bybit OHLCV into data/cache")
    fetch.add_argument("--config", default="configs/backtest_v1.yaml")
    fetch.add_argument("--set", choices=["A", "B", "C", "all"], default="all")
    fetch.add_argument("--force", action="store_true")
    fetch.add_argument(
        "--synthetic",
        action="store_true",
        help="Write synthetic OHLCV instead of calling Bybit (offline smoke test)",
    )

    bt = sub.add_parser("backtest", help="Run MTF trend backtest for a data set")
    bt.add_argument("--config", default="configs/backtest_v1.yaml")
    bt.add_argument("--set", choices=["A", "B", "C"], default="B")
    bt.add_argument("--force-fetch", action="store_true")
    bt.add_argument(
        "--synthetic",
        action="store_true",
        help="Use synthetic data if cache missing / for offline runs",
    )

    return p.parse_args(argv)


def _set_bounds(cfg, set_name: str) -> tuple[str, str]:
    # Warmup: need history before set start for EMA
    warm_days = max(cfg.daily_ema * 2, 120)
    start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC") - pd.Timedelta(days=warm_days)
    end = cfg.sets[set_name].end
    return start.strftime("%Y-%m-%d"), end


def cmd_fetch(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    names = ["A", "B", "C"] if args.set == "all" else [args.set]
    for name in names:
        start, end = _set_bounds(cfg, name)
        print(f"Fetching set {name}: {start} → {end}")
        frames, source = _load_or_fetch_frames(
            cfg, name, force=args.force, synthetic=args.synthetic
        )
        print(f"  data_source: {source}")
        for interval, df in frames.items():
            print(f"  {interval}: {len(df)} bars")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    frames, source = _load_or_fetch_frames(
        cfg, args.set, force=args.force_fetch, synthetic=args.synthetic
    )

    params = StrategyParams(
        daily_ema=cfg.daily_ema,
        h4_ema=cfg.h4_ema,
        m15_ema=cfg.m15_ema,
        stop_loss_pct=cfg.stop_loss_pct,
        take_profit_pct=cfg.take_profit_pct,
    )
    prepared = prepare_frames(frames["1d"], frames["4h"], frames["15m"], params)

    # Restrict evaluation window to the declared set (after warmup signals exist)
    set_start = pd.Timestamp(cfg.sets[args.set].start, tz="UTC")
    set_end = pd.Timestamp(cfg.sets[args.set].end, tz="UTC") + pd.Timedelta(days=1)
    prepared = prepared[(prepared.index >= set_start) & (prepared.index < set_end)]
    if prepared.empty:
        print("No bars in evaluation window", file=sys.stderr)
        return 1

    result = run_backtest(
        prepared,
        initial_equity=cfg.initial_equity,
        leverage=cfg.leverage,
        risk_per_trade_pct=cfg.risk_per_trade_pct,
        stop_loss_pct=cfg.stop_loss_pct,
        take_profit_pct=cfg.take_profit_pct,
        fee_rate=cfg.fee_rate_per_side,
        slippage_pct=cfg.slippage_pct_per_side,
    )
    metrics = compute_metrics(
        result,
        min_trades=cfg.min_trades,
        max_drawdown_pct_limit=cfg.max_drawdown_pct,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("artifacts/backtests") / f"{stamp}_set{args.set}"
    out_dir.mkdir(parents=True, exist_ok=True)

    trades_df = trades_to_frame(result.trades)
    trades_df.to_csv(out_dir / "trades.csv", index=False)
    result.equity_curve.to_csv(out_dir / "equity_curve.csv", header=True)
    monthly = monthly_returns(result.trades, cfg.initial_equity)
    monthly.to_csv(out_dir / "monthly_returns_pct.csv", header=["monthly_return_pct"])

    payload = {
        "set": args.set,
        "config": args.config,
        "eval_start": cfg.sets[args.set].start,
        "eval_end": cfg.sets[args.set].end,
        "bars": len(prepared),
        "synthetic": bool(args.synthetic) or source == "synthetic",
        "data_source": source,
        "metrics": metrics_to_dict(metrics),
        "final_equity": result.final_equity,
    }
    (out_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"\nArtifacts: {out_dir}")
    print(f"GATE: {'PASS' if metrics.gate_pass else 'FAIL'}")
    # Synthetic runs are smoke tests only — do not fail CI on strategy gate
    if args.synthetic or source == "synthetic":
        return 0
    return 0 if metrics.gate_pass or args.set != "B" else 2


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "fetch-data":
        raise SystemExit(cmd_fetch(args))
    if args.command == "backtest":
        raise SystemExit(cmd_backtest(args))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
