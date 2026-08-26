from __future__ import annotations

import argparse
import json
import subprocess
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
from autotrade.strategy.registry import LOGIC_META, known_logic_ids, prepare_strategy
from autotrade.research.log import record_backtest_run, refresh_index
from autotrade.eval import prepare_eval_lock, run_formal_eval


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
            path = cache / f"{cfg.symbol}_synthetic_{interval}_{start}_{end}.csv"
            frames[interval] = load_ohlcv(path)
        return frames, "synthetic"

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

    bt = sub.add_parser("backtest", help="Run strategy backtest for a data set")
    bt.add_argument("--config", default="configs/backtest_v1.yaml")
    bt.add_argument("--set", choices=["A", "B", "C"], default="B")
    bt.add_argument("--force-fetch", action="store_true")
    bt.add_argument(
        "--synthetic",
        action="store_true",
        help="Use synthetic data if cache missing / for offline runs",
    )
    bt.add_argument(
        "--logic-id",
        default="mtf_ema_pullback_v1",
        choices=known_logic_ids(),
        help="Strategy / logic variant",
    )
    bt.add_argument(
        "--hypothesis-id",
        default=None,
        help="Override hypothesis ID (default: from logic-id registry)",
    )
    bt.add_argument(
        "--no-research-log",
        action="store_true",
        help="Do not append to docs/research registry",
    )

    res = sub.add_parser("research", help="Research knowledge base")
    res_sub = res.add_subparsers(dest="research_command", required=True)
    res_sub.add_parser("refresh-index", help="Regenerate docs/research/INDEX.md from registry")

    ep = sub.add_parser(
        "eval-prepare",
        help="Fetch REAL market data and write eval/locks (formal eval environment)",
    )
    ep.add_argument("--config", default="configs/eval_v1.yaml")
    ep.add_argument("--sets", default="A,B,C", help="Comma-separated sets, e.g. A,B,C")
    ep.add_argument("--force", action="store_true", help="Re-download even if cache exists")

    ev = sub.add_parser(
        "eval",
        help="Formal evaluation on locked real data (synthetic forbidden)",
    )
    ev.add_argument("--config", default="configs/eval_v1.yaml")
    ev.add_argument(
        "--logic-id",
        required=True,
        help="One id or comma-separated list",
    )
    ev.add_argument("--set", choices=["A", "B", "C"], default=None, help="Default: primary gate B")
    ev.add_argument(
        "--no-research-log",
        action="store_true",
        help="Do not append to docs/research registry",
    )

    demo = sub.add_parser(
        "demo",
        help="SH-01 rest filters on Bybit testnet (dry-run unless --submit)",
    )
    demo.add_argument("--config", default="configs/demo_sh01.yaml")
    demo.add_argument(
        "--order-logic",
        default=None,
        help="Which logic may place orders (default: config order_logic). The other is shadow.",
    )
    demo.add_argument(
        "--submit",
        action="store_true",
        help="Send testnet orders. Requires keys in secrets/demo/bybit.txt. Never live.",
    )
    demo.add_argument(
        "--once",
        action="store_true",
        help="One 15m cycle then exit (for checks). Default is to keep polling.",
    )
    demo.add_argument(
        "--data-source",
        choices=("bybit", "vision"),
        default="bybit",
        help="Public klines. --submit requires bybit.",
    )
    demo.add_argument("--poll-seconds", type=float, default=15.0)

    sub.add_parser(
        "secrets-init",
        help="Create secrets/demo/bybit.txt, make it editable, keep keys out of git",
    )

    return p.parse_args(argv)


def _set_bounds(cfg, set_name: str) -> tuple[str, str]:
    warm_days = max(cfg.daily_ema * 2, 220)
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
    meta = LOGIC_META[args.logic_id]
    hypothesis_id = args.hypothesis_id or meta["hypothesis_id"]

    frames, source = _load_or_fetch_frames(
        cfg, args.set, force=args.force_fetch, synthetic=args.synthetic
    )

    prepared = prepare_strategy(
        args.logic_id, frames["1d"], frames["4h"], frames["15m"], cfg=cfg
    )

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
        sizing_mode=cfg.sizing_mode,
        margin_per_trade=cfg.margin_per_trade,
        risk_per_trade_usdt=cfg.risk_per_trade_usdt,
    )
    metrics = compute_metrics(
        result,
        min_trades=cfg.min_trades,
        max_drawdown_pct_limit=cfg.max_drawdown_pct,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("artifacts/backtests") / f"{stamp}_set{args.set}_{args.logic_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    trades_df = trades_to_frame(result.trades)
    trades_df.to_csv(out_dir / "trades.csv", index=False)
    result.equity_curve.to_csv(out_dir / "equity_curve.csv", header=True)
    monthly = monthly_returns(result.trades, cfg.initial_equity)
    monthly.to_csv(out_dir / "monthly_returns_pct.csv", header=["monthly_return_pct"])

    payload = {
        "set": args.set,
        "config": args.config,
        "logic_id": args.logic_id,
        "hypothesis_id": hypothesis_id,
        "eval_start": cfg.sets[args.set].start,
        "eval_end": cfg.sets[args.set].end,
        "bars": len(prepared),
        "synthetic": bool(args.synthetic) or source == "synthetic",
        "data_source": source,
        "metrics": metrics_to_dict(metrics),
        "final_equity": result.final_equity,
    }
    (out_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not args.no_research_log:
        synthetic = bool(args.synthetic) or source == "synthetic"
        learnings = _default_learnings(
            hypothesis_id=hypothesis_id, gate_pass=metrics.gate_pass, synthetic=synthetic
        )
        run = record_backtest_run(
            payload=payload,
            artifacts_dir=out_dir,
            hypothesis_id=hypothesis_id,
            logic_id=args.logic_id,
            hypothesis_name=meta["name"],
            distortion_ids=list(meta.get("distortion_ids") or []),
            logic_summary=_logic_summary(cfg, args.logic_id),
            learnings=learnings,
            next_actions=_next_actions(hypothesis_id, metrics.gate_pass, synthetic),
            notes="synthetic smoke" if synthetic else "",
        )
        print(f"Research log: {run['entry_doc']} (run_id={run['run_id']})")

    print(json.dumps(payload, indent=2))
    print(f"\nArtifacts: {out_dir}")
    print(f"GATE: {'PASS' if metrics.gate_pass else 'FAIL'}")
    if args.synthetic or source == "synthetic":
        return 0
    return 0 if metrics.gate_pass or args.set != "B" else 2


def _logic_summary(cfg, logic_id: str) -> dict:
    if logic_id == "mtf_ema_pullback_v1":
        return {
            "daily": f"EMA{cfg.daily_ema} 方向フィルタ",
            "h4": f"EMA{cfg.h4_ema} 方向フィルタ",
            "m15_entry": f"EMA{cfg.m15_ema} 押し目 + 陽線/陰線",
            "exit_stop": f"固定 {cfg.stop_loss_pct}%",
            "exit_tp": f"固定 {cfg.take_profit_pct}%",
            "leverage": cfg.leverage,
        }
    if logic_id == "cost_gate_v1":
        return {
            "change_from": "H01",
            "rule": "ATRが往復コスト×1.5未満ならスキップ",
            "exit_stop": f"固定 {cfg.stop_loss_pct}%",
            "exit_tp": f"固定 {cfg.take_profit_pct}%",
        }
    if logic_id == "vol_scaled_trend_v1":
        return {
            "daily": "SMA200 レジーム",
            "h4": "EMA20 方向",
            "m15": "EMA押し目執行",
            "exit": "ATRトレール 2.5x、固定利確なし",
            "size": "ATRストップ基準リスク%",
        }
    if logic_id == "donchian_20_10_v1":
        return {
            "entry": "日足20 Donchian ブレイク",
            "exit": "日足10 Donchian 逆側 + ATRストップ",
            "long_only": False,
        }
    if logic_id == "donchian_20_10_long_only":
        return {
            "entry": "日足20 Donchian 上抜けのみ",
            "exit": "日足10 Donchian 下抜け + ATRストップ",
            "long_only": True,
        }
    if logic_id == "donchian_20_10_long_v2":
        return {
            "entry": "新規上抜け初日のみ + 4H確認（陽線 or 4H Donchian上）",
            "exit": "日足10 Donchian 下抜け + ATRストップ",
            "long_only": True,
            "change_from": "donchian_20_10_long_only",
            "hypothesis": "HYP-002",
        }
    if logic_id == "fake_then_rebreak_v1":
        return {
            "entry": "圧縮→HH20だまし→再突破初日 + 4H陽線",
            "exit": "日足10 Donchian 下抜け + ATRストップ",
            "spot": "SPOT-D001",
            "hypothesis": "HYP-009",
        }
    if logic_id == "fake_then_retest_v1":
        return {
            "entry": "だまし後本突破水準の再テスト支え + 4H陽線",
            "exit": "日足10 Donchian 下抜け + ATRストップ",
            "spot": "SPOT-D001",
            "hypothesis": "HYP-010",
        }
    if logic_id == "near_high_expanded_v1":
        return {
            "entry": "20日高値帯 × ATR%拡大 × SMA50上（新規成立日）+ 4H陽線",
            "exit": "日足10 Donchian 下抜け + ATRストップ",
            "spot": "SPOT-R001",
            "hypothesis": "HYP-011",
        }
    return {"logic_id": logic_id}


def _default_learnings(*, hypothesis_id: str, gate_pass: bool, synthetic: bool) -> dict:
    if synthetic:
        return {
            "one_liner": "合成データ smoke。採用判断に使わない。",
            "summary": "パイプライン・ロジック実装の動作確認。次は実データ Set B。",
            "keep": ["実装パスと research / workstream への自動蓄積"],
            "discard": ["合成でのゲートPASSを意思決定に使うこと"],
        }
    if hypothesis_id == "H01" and not gate_pass:
        return {
            "one_liner": "コスト込みで期待値マイナス",
            "summary": "固定利確と緩い押し目で費用負けの可能性。",
            "structural": [
                "トレンド狙いなのに固定利確で大勝ちを切る",
                "押し目条件が緩く回転が増える",
            ],
            "discard": ["固定%利確のまま本番"],
        }
    if gate_pass:
        return {"summary": "Set B ゲート合格。Set C で耐久確認へ。"}
    return {"summary": "ゲート不合格。知見を entries に追記すること。"}


def _next_actions(hypothesis_id: str, gate_pass: bool, synthetic: bool) -> list[str]:
    if synthetic:
        return ["実データ（Bybit or Vision）で Set B を再実行", "workstream README の現状を更新"]
    if gate_pass:
        return ["Set C で耐久確認", "demo 執行の設計"]
    if hypothesis_id == "H01":
        return ["L-COST", "L-MOM-VOL", "L-BREAK"]
    return ["MARKET_EDGE_MAP の優先バッチを参照"]


def cmd_research(args: argparse.Namespace) -> int:
    if args.research_command == "refresh-index":
        refresh_index()
        print("Updated docs/research/INDEX.md")
        return 0
    return 1


def cmd_eval_prepare(args: argparse.Namespace) -> int:
    sets = [s.strip() for s in args.sets.split(",") if s.strip()]
    lock = prepare_eval_lock(args.config, sets=sets, force=args.force)
    print(json.dumps(lock, indent=2))
    print("\nWrote eval/locks/eval_v1.lock.yaml")
    sources = {k: v.get("data_source") for k, v in lock.get("datasets", {}).items()}
    print(f"Data sources: {sources}")
    if any(s == "binance_vision" for s in sources.values()):
        print(
            "NOTE: Using Binance Vision (Bybit blocked). "
            "Re-confirm on Bybit locally before any live decision.",
            file=sys.stderr,
        )
    return 0


DEMO_KEYS_PATH = Path("secrets/demo/bybit.txt")
DEMO_KEYS_TEMPLATE = """# Demo / testnet keys. Open THIS file in the left Explorer.
# Do not put keys in *.example (those go to GitHub).
# Do not git add this file after filling keys.

BYBIT_ENV=demo
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_BASE_URL=https://api-testnet.bybit.com
"""


def cmd_secrets_init(_args: argparse.Namespace) -> int:
    from autotrade.exec.secrets import protect_from_commit

    DEMO_KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DEMO_KEYS_PATH.exists():
        DEMO_KEYS_PATH.write_text(DEMO_KEYS_TEMPLATE, encoding="utf-8")
        print(f"created {DEMO_KEYS_PATH}")
    else:
        print(f"exists {DEMO_KEYS_PATH}")
    DEMO_KEYS_PATH.chmod(0o644)
    protect_from_commit(DEMO_KEYS_PATH)
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], check=False)
    print(
        "左の Explorer で secrets/demo/bybit.txt を開いてキーを書いてください。"
        " *.example には書かないでください（GitHub に載ります）。"
    )
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    logic_ids = [x.strip() for x in args.logic_id.split(",") if x.strip()]
    unknown = [x for x in logic_ids if x not in LOGIC_META]
    if unknown:
        print(f"Unknown logic-id: {unknown}. Known: {known_logic_ids()}", file=sys.stderr)
        return 1

    exit_code = 0
    for logic_id in logic_ids:
        try:
            payload = run_formal_eval(
                config_path=args.config,
                logic_id=logic_id,
                set_name=args.set,
                write_research_log=not args.no_research_log,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"EVAL ERROR [{logic_id}]: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(json.dumps(payload, indent=2))
        print(f"Report: {payload.get('report_path')}")
        print(f"GATE: {'PASS' if payload.get('gate_pass') else 'FAIL'}")
        if args.set in (None, "B") and not payload.get("gate_pass"):
            exit_code = 2
    return exit_code


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "fetch-data":
        raise SystemExit(cmd_fetch(args))
    if args.command == "backtest":
        raise SystemExit(cmd_backtest(args))
    if args.command == "research":
        raise SystemExit(cmd_research(args))
    if args.command == "eval-prepare":
        raise SystemExit(cmd_eval_prepare(args))
    if args.command == "eval":
        raise SystemExit(cmd_eval(args))
    if args.command == "demo":
        from autotrade.exec.loop import run_demo

        raise SystemExit(
            run_demo(
                args.config,
                submit=args.submit,
                once=args.once,
                order_logic=args.order_logic,
                data_source=args.data_source,
                poll_seconds=args.poll_seconds,
            )
        )
    if args.command == "secrets-init":
        raise SystemExit(cmd_secrets_init(args))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
