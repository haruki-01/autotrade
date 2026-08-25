"""Run the SH-01 slow pack across the eval_v2 symbol basket.

Each symbol is backtested on its own, then every trade is merged into a single
equity curve ordered by exit time. That merge is only legitimate because
``fixed_margin`` sizing makes position size independent of running equity, so
the per-symbol runs really are independent.

Usage:
    python scripts/run_slow_pack.py --config configs/eval_v3_btc.yaml --set B
    python scripts/run_slow_pack.py --config configs/eval_v3_btc.yaml --set B \\
        --campaign ev-dd --logics sh01n_center,sh01_base
"""

from __future__ import annotations

import argparse
import hashlib
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


def env_fingerprint() -> dict[str, str]:
    """Versions of the libraries that turn the locked bytes into trades.

    The lock pins the input data. It does not pin the arithmetic, and a rebuilt
    VM was enough to move eleven of twenty-three variants on identical input,
    so the reader of a report needs to know which arithmetic produced it.
    """
    import numpy

    return {
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
        "numpy": numpy.__version__,
    }


def portfolio_metrics(
    trades: list[dict],
    *,
    initial_equity: float,
    min_trades: int,
    max_dd_limit: float,
    months: float,
    min_per_month: float = 0.0,
    apply_trade_rate_gate: bool = True,
) -> dict:
    """Metrics on the merged book rather than on any single symbol.

    ``min_trades`` is a sample-size floor: below it expectancy cannot be
    measured, so the verdict is "cannot tell" rather than "fails".
    ``min_per_month`` is reported either way. It is a pass/fail gate only when
    ``apply_trade_rate_gate`` is true (the 2026-08-24 operational requirement).
    The 2026-08-25 campaign judges cost-after EV and drawdown; monthly 50 is
    not a gate on that path.
    """
    n = len(trades)
    if n == 0:
        return {
            "trades": 0,
            "trades_per_month": 0.0,
            "months_meeting_rate_pct": 0.0,
            "avg_trade_pnl": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
            "payoff_ratio": None,
            "total_fees": 0.0,
            "total_funding": 0.0,
            "gate_pass": False,
            "gate_failures": ["min_trades", "expectancy"]
            + (["trade_rate"] if apply_trade_rate_gate else []),
            "yaml_gate_failures": ["min_trades", "expectancy", "trade_rate"],
            "ev_dd_pass": False,
            "sample_hold": True,
            "campaign": "ev-dd" if not apply_trade_rate_gate else "yaml",
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

    per_month = n / months if months > 0 else 0.0
    # The average can hide a strategy that fires in bursts, so count the months
    # that actually clear the rate rather than trusting the mean.
    entry_months = pd.DatetimeIndex(df["entry_time"]).to_period("M")
    counts = entry_months.value_counts()
    n_months = int(round(months))
    meeting = int((counts >= min_per_month).sum()) if min_per_month > 0 else 0
    meeting_pct = 100.0 * meeting / n_months if n_months else 0.0

    yaml_failures = []
    if n < min_trades:
        yaml_failures.append("min_trades")
    if avg <= 0:
        yaml_failures.append("expectancy")
    if dd > max_dd_limit:
        yaml_failures.append("drawdown")
    if min_per_month > 0 and per_month < min_per_month:
        yaml_failures.append("trade_rate")

    if apply_trade_rate_gate:
        failures = yaml_failures
    else:
        failures = ev_dd_fail
    ev_dd_fail = [f for f in yaml_failures if f in ("expectancy", "drawdown")]

    return {
        "trades": n,
        "trades_per_month": per_month,
        "months_meeting_rate_pct": meeting_pct,
        "avg_trade_pnl": avg,
        "total_return_pct": float(equity.iloc[-1] / initial_equity - 1.0) * 100.0,
        "max_drawdown_pct": float(dd),
        "win_rate_pct": float(len(wins) / n * 100.0),
        "payoff_ratio": payoff,
        "total_fees": float(df["fee"].sum()),
        "total_funding": float(df["funding"].sum()),
        "gate_pass": not failures,
        "gate_failures": failures,
        "yaml_gate_failures": yaml_failures,
        "ev_dd_pass": not ev_dd_fail,
        "sample_hold": n < min_trades,
        "campaign": "ev-dd" if not apply_trade_rate_gate else "yaml",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v2.yaml")
    ap.add_argument("--set", dest="set_name", required=True)
    ap.add_argument("--logics", default="")
    ap.add_argument("--tag", default="slow-pack")
    ap.add_argument("--lock", default=str(MULTI_LOCK_PATH))
    ap.add_argument(
        "--campaign",
        choices=("yaml", "ev-dd"),
        default="yaml",
        help=(
            "yaml: eval yaml のゲートをそのまま使う（月50含む）。"
            "ev-dd: 費用後EV>0 と DD だけを合否にする。月50は報告のみ。"
            "min_trades 未達は判定保留（サンプル）として印を付ける。"
        ),
    )
    ap.add_argument(
        "--risk-usdt",
        type=float,
        default=None,
        help="risk_per_trade_usdt を上書きする。建玉の大きさだけを変えたいとき用。",
    )
    ap.add_argument(
        "--min-trades",
        type=int,
        default=None,
        help=(
            "ゲートの min_trades を上書きする。銘柄数が eval_v2 と違うときだけ使う。"
            "使ったらレポートに明記される。"
        ),
    )
    args = ap.parse_args()
    apply_rate = args.campaign == "yaml"

    cfg, _, raw = load_eval_config(args.config)
    lock_path = Path(args.lock)
    if args.lock == str(MULTI_LOCK_PATH) and Path(args.config).name.startswith("eval_v3"):
        lock_path = Path("eval/locks/eval_v3_btc.lock.yaml")
        args.lock = str(lock_path)
    risk_usdt = args.risk_usdt if args.risk_usdt is not None else cfg.risk_per_trade_usdt
    min_trades = args.min_trades if args.min_trades is not None else cfg.min_trades
    lock_bytes = Path(args.lock).read_bytes()
    lock = yaml.safe_load(lock_bytes.decode("utf-8"))
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
    set_months = (set_end - set_start).days / 30.4375

    print(f"set={set_name} symbols={len(symbols)} logics={len(logic_ids)}", flush=True)
    # Only the EH-06 veto variants read derivatives, and their history starts
    # years after the price history does. Loading them anyway would bar a
    # long-history run from testing the variants that never needed them.
    any_deriv = any(lid in NEEDS_DERIVATIVES for lid in logic_ids)

    data: dict[str, tuple[pd.DataFrame, pd.DataFrame | None]] = {}
    for symbol in symbols:
        frames = load_multi_frames(lock, set_name, symbol)
        m15 = frames["15m"]
        deriv = load_multi_derivatives(lock, set_name, symbol, m15.index) if any_deriv else None
        data[symbol] = (m15, deriv)
        print(f"  {symbol}: {len(m15)} bars", flush=True)

    env = env_fingerprint()
    env["lock"] = f"{Path(args.lock).name}@{hashlib.sha256(lock_bytes).hexdigest()[:12]}"
    print("env: " + ", ".join(f"{k} {v}" for k, v in env.items()), flush=True)

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
                risk_per_trade_usdt=risk_usdt,
            )
            per_symbol[symbol] = len(result.trades)
            for t in result.trades:
                d = asdict(t) if hasattr(t, "__dataclass_fields__") else dict(t.__dict__)
                d["symbol"] = symbol
                all_trades.append(d)

        m = portfolio_metrics(
            all_trades,
            initial_equity=cfg.initial_equity,
            min_trades=min_trades,
            max_dd_limit=cfg.max_drawdown_pct,
            months=set_months,
            min_per_month=cfg.min_trades_per_month,
            apply_trade_rate_gate=apply_rate,
        )
        row = {
            "logic_id": logic_id,
            "hypothesis_id": hyp,
            "name": name,
            "knob": knob,
            "why": why,
            "set": set_name,
            "symbols": symbols,
            "risk_per_trade_usdt": risk_usdt,
            "min_trades_used": min_trades,
            "campaign": args.campaign,
            "env": env,
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

        if args.campaign == "ev-dd":
            flag = "PASS" if m["ev_dd_pass"] else "FAIL"
            if m["sample_hold"]:
                flag += "/HOLD"
        else:
            flag = "PASS" if m["gate_pass"] else "FAIL"
        print(
            f"[{i:3d}/{len(logic_ids)}] {logic_id:22s} {flag} "
            f"n={m['trades']:4d} ({m['trades_per_month']:5.1f}/月) "
            f"EV={m['avg_trade_pnl']:+.3f} "
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
        f"min_trades={min_trades}（全銘柄合計）"
        + ("（★上書き、既定 %d）" % cfg.min_trades if min_trades != cfg.min_trades else "")
        + f", max_dd={cfg.max_drawdown_pct}%, risk={risk_usdt} USDT/trade"
        + (
            f", 最低 {cfg.min_trades_per_month:.0f} エントリー/月"
            if cfg.min_trades_per_month and args.campaign == "yaml"
            else ""
        )
        + (
            f", campaign=ev-dd（月{cfg.min_trades_per_month:.0f}回は報告のみ・合否に使わない）"
            if args.campaign == "ev-dd"
            else ""
        )
        + ("（★上書き）" if risk_usdt != cfg.risk_per_trade_usdt else ""),
        "",
        "実行環境: " + " / ".join(f"{k} {v}" for k, v in env.items()),
        "",
        "| logic | ノブ | n | 月あたり | EV | 勝率 | DD | 総リターン | EV+DD | サンプル | 落ちた条件 |",
        "|-------|------|---|---------|----|------|----|-----------|-------|----------|-----------|",
    ]
    for r in rows:
        evdd = "PASS" if r.get("ev_dd_pass") else "FAIL"
        sample = "判定保留" if r.get("sample_hold") else "ok"
        drops = r.get("gate_failures") or []
        md.append(
            f"| `{r['logic_id']}` | {r['knob']} | {r['trades']} "
            f"| {r['trades_per_month']:.1f} | {r['avg_trade_pnl']:+.3f} "
            f"| {r['win_rate_pct']:.1f}% | {r['max_drawdown_pct']:.1f}% "
            f"| {r['total_return_pct']:+.1f}% | {evdd} | {sample} "
            f"| {', '.join(drops) or '—'} |"
        )
    base.with_suffix(".md").write_text("\n".join(md) + "\n", "utf-8")

    if args.campaign == "ev-dd":
        npass = sum(1 for r in rows if r.get("ev_dd_pass"))
        print(f"\nEV+DD PASS {npass}/{len(rows)}  →  {base.with_suffix('.md')}")
        for r in rows:
            mark = "PASS" if r.get("ev_dd_pass") else "FAIL"
            hold = " HOLD" if r.get("sample_hold") else ""
            print(
                f"  {r['logic_id']}  {mark}{hold}  "
                f"EV={r['avg_trade_pnl']:+.3f} n={r['trades']}"
            )
    else:
        npass = sum(1 for r in rows if r["gate_pass"])
        print(f"\nPASS {npass}/{len(rows)}  →  {base.with_suffix('.md')}")
        for r in rows:
            if r["gate_pass"]:
                print(f"  {r['logic_id']}  EV={r['avg_trade_pnl']:+.3f} n={r['trades']}")


if __name__ == "__main__":
    main()
