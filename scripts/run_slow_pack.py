"""Run the SH-01 slow pack across the eval_v2 symbol basket.

Each symbol is backtested on its own, then every trade is merged into a single
equity curve ordered by exit time. That merge is only legitimate because
``fixed_margin`` sizing makes position size independent of running equity, so
the per-symbol runs really are independent.

Usage:
    python scripts/run_slow_pack.py --set B
    python scripts/run_slow_pack.py --set B --logics sh01_base,sh01_veto_1p0
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.backtest.engine import run_backtest  # noqa: E402
from autotrade.backtest.metrics import max_drawdown_pct  # noqa: E402
from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.eval.multi import (  # noqa: E402
    MULTI_LOCK_PATH,
    load_multi_derivatives,
    load_multi_frames,
    validate_multi_lock,
)
from autotrade.strategy.slow import CYCLE_SLOW, NEEDS_DERIVATIVES, prepare_slow  # noqa: E402

REPORTS_DIR = Path("eval/reports")
ARTIFACTS_ROOT = Path("artifacts/evals")


def portfolio_metrics(
    trades: list[dict], *, initial_equity: float, min_trades: int, max_dd_limit: float
) -> dict:
    """Metrics on the merged book rather than on any single symbol."""
    n = len(trades)
    if n == 0:
        return {
            "trades": 0,
            "avg_trade_pnl": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
            "payoff_ratio": None,
            "total_fees": 0.0,
            "total_funding": 0.0,
            "gate_pass": False,
            "gate_failures": ["min_trades", "expectancy"],
        }

    df = pd.DataFrame(trades).sort_values("exit_time")
    equity = initial_equity + df["pnl"].cumsum()
    curve = pd.Series(equity.to_numpy(), index=pd.DatetimeIndex(df["exit_time"]))
    dd = abs(max_drawdown_pct(curve))

    pnls = df["pnl"].to_numpy()
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    avg = float(pnls.mean())
    payoff = (
        float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) and losses.mean() else None
    )

    failures = []
    if n < min_trades:
        failures.append("min_trades")
    if avg <= 0:
        failures.append("expectancy")
    if dd > max_dd_limit:
        failures.append("drawdown")

    return {
        "trades": n,
        "avg_trade_pnl": avg,
        "total_return_pct": float(equity.iloc[-1] / initial_equity - 1.0) * 100.0,
        "max_drawdown_pct": float(dd),
        "win_rate_pct": float(len(wins) / n * 100.0),
        "payoff_ratio": payoff,
        "total_fees": float(df["fee"].sum()),
        "total_funding": float(df["funding"].sum()),
        "gate_pass": not failures,
        "gate_failures": failures,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v2.yaml")
    ap.add_argument("--set", dest="set_name", required=True)
    ap.add_argument("--logics", default="")
    ap.add_argument("--tag", default="slow-pack")
    ap.add_argument("--lock", default=str(MULTI_LOCK_PATH))
    args = ap.parse_args()

    cfg, _, raw = load_eval_config(args.config)
    lock = yaml.safe_load(Path(args.lock).read_text(encoding="utf-8"))
    set_name = args.set_name

    errors = validate_multi_lock(lock, set_name)
    if errors:
        raise SystemExit("lock validation failed:\n  " + "\n  ".join(errors[:10]))

    symbols = list(lock["datasets"][set_name]["symbols"])
    logic_ids = (
        [x.strip() for x in args.logics.split(",") if x.strip()]
        if args.logics
        else list(CYCLE_SLOW)
    )

    set_start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
    set_end = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)

    print(f"set={set_name} symbols={len(symbols)} logics={len(logic_ids)}", flush=True)
    data: dict[str, tuple[pd.DataFrame, pd.DataFrame | None]] = {}
    for symbol in symbols:
        frames = load_multi_frames(lock, set_name, symbol)
        m15 = frames["15m"]
        deriv = load_multi_derivatives(lock, set_name, symbol, m15.index)
        data[symbol] = (m15, deriv)
        print(f"  {symbol}: {len(m15)} bars", flush=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_root = ARTIFACTS_ROOT / f"{stamp}_slow_set{set_name}"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for i, logic_id in enumerate(logic_ids, 1):
        params, hyp, name, knob, why = CYCLE_SLOW[logic_id]
        needs_deriv = logic_id in NEEDS_DERIVATIVES
        all_trades: list[dict] = []
        per_symbol: dict[str, int] = {}

        for symbol, (m15, deriv) in data.items():
            prepared = prepare_slow(logic_id, m15, deriv if needs_deriv else None)
            window = prepared[(prepared.index >= set_start) & (prepared.index < set_end)]
            if window.empty:
                continue
            result = run_backtest(
                window,
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
            per_symbol[symbol] = len(result.trades)
            for t in result.trades:
                d = asdict(t) if hasattr(t, "__dataclass_fields__") else dict(t.__dict__)
                d["symbol"] = symbol
                all_trades.append(d)

        m = portfolio_metrics(
            all_trades,
            initial_equity=cfg.initial_equity,
            min_trades=cfg.min_trades,
            max_dd_limit=cfg.max_drawdown_pct,
        )
        row = {
            "logic_id": logic_id,
            "hypothesis_id": hyp,
            "name": name,
            "knob": knob,
            "why": why,
            "set": set_name,
            "symbols": symbols,
            "trades_per_symbol": per_symbol,
            **m,
        }
        rows.append(row)

        out_dir = artifacts_root / f"set{set_name}_{logic_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        if all_trades:
            pd.DataFrame(all_trades).to_csv(out_dir / "trades.csv", index=False)
        (out_dir / "metrics.json").write_text(json.dumps(row, indent=2, default=str), "utf-8")
        row["artifacts_dir"] = str(out_dir)

        flag = "PASS" if m["gate_pass"] else "FAIL"
        print(
            f"[{i:3d}/{len(logic_ids)}] {logic_id:22s} {flag} "
            f"n={m['trades']:4d} EV={m['avg_trade_pnl']:+.3f} "
            f"DD={m['max_drawdown_pct']:.1f}% ret={m['total_return_pct']:+.1f}%",
            flush=True,
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = REPORTS_DIR / f"{day}-{args.tag}-set{set_name}"
    base.with_suffix(".json").write_text(json.dumps(rows, indent=2, default=str), "utf-8")

    md = [
        f"# SH-01 slow pack — Set {set_name}",
        "",
        f"銘柄: {', '.join(symbols)}  ／  ロジック {len(rows)} 本  ／  "
        f"min_trades={cfg.min_trades}（全銘柄合計）, max_dd={cfg.max_drawdown_pct}%",
        "",
        "| logic | ノブ | n | EV | 勝率 | DD | 総リターン | 判定 |",
        "|-------|------|---|----|------|----|-----------|------|",
    ]
    for r in rows:
        md.append(
            f"| `{r['logic_id']}` | {r['knob']} | {r['trades']} | {r['avg_trade_pnl']:+.3f} "
            f"| {r['win_rate_pct']:.1f}% | {r['max_drawdown_pct']:.1f}% "
            f"| {r['total_return_pct']:+.1f}% | {'PASS' if r['gate_pass'] else 'FAIL'} |"
        )
    base.with_suffix(".md").write_text("\n".join(md) + "\n", "utf-8")

    npass = sum(1 for r in rows if r["gate_pass"])
    print(f"\nPASS {npass}/{len(rows)}  →  {base.with_suffix('.md')}")
    for r in rows:
        if r["gate_pass"]:
            print(f"  {r['logic_id']}  EV={r['avg_trade_pnl']:+.3f} n={r['trades']}")


if __name__ == "__main__":
    main()
