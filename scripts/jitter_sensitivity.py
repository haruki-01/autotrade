"""Measure how much a strategy's result moves under negligible price noise.

Motivation: rebuilding the VM changed eleven of twenty-three SH-01 variants on
byte-identical input data. That points at comparisons decided by the last bits
of a float -- a close landing exactly on a channel, a bar touching a stop to
the tick. Whichever library version tipped those ties, a result that depends on
them is not a result.

So perturb every price by a relative amount far below anything tradable
(1e-6 = 0.0001%, against a round-trip cost of 0.15%) and rerun. If the strategy
is reading a real move, the numbers barely register it. If the numbers swing,
the backtest is living on exact touches and its fills are fiction.

Usage:
    python scripts/jitter_sensitivity.py --set C --logics sh01_tp_4atr --seeds 8
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.backtest.engine import run_backtest  # noqa: E402
from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.eval.multi import (  # noqa: E402
    load_multi_derivatives,
    load_multi_frames,
    validate_multi_lock,
)
from autotrade.strategy.slow import CYCLE_SLOW, NEEDS_DERIVATIVES, prepare_slow  # noqa: E402

PRICE_COLS = ("open", "high", "low", "close")


def jitter(frame: pd.DataFrame, rel: float, seed: int) -> pd.DataFrame:
    """Scale each bar by 1 +/- rel, keeping the bar internally consistent.

    One factor per bar rather than one per column: moving a high below its own
    close would test malformed data, not sensitivity.
    """
    rng = np.random.default_rng(seed)
    out = frame.copy()
    factor = 1.0 + rng.uniform(-rel, rel, size=len(out))
    for col in PRICE_COLS:
        if col in out.columns:
            out[col] = out[col].to_numpy() * factor
    return out


def run_one(cfg, frame: pd.DataFrame, logic_id: str, deriv, start, end) -> tuple[int, float]:
    prepared = prepare_slow(logic_id, frame, deriv)
    window = prepared[(prepared.index >= start) & (prepared.index < end)]
    if window.empty:
        return 0, 0.0
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
    pnl = sum(asdict(t)["pnl"] for t in result.trades)
    return len(result.trades), pnl


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v2.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v2.lock.yaml")
    ap.add_argument("--set", dest="set_name", required=True)
    ap.add_argument("--logics", required=True)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--rel", type=float, default=1e-6)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    lock = yaml.safe_load(Path(args.lock).read_text(encoding="utf-8"))
    set_name = args.set_name
    errors = validate_multi_lock(lock, set_name)
    if errors:
        raise SystemExit("lock validation failed:\n  " + "\n  ".join(errors[:10]))

    symbols = list(lock["datasets"][set_name]["symbols"])
    start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
    end = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)

    data = {}
    for symbol in symbols:
        m15 = load_multi_frames(lock, set_name, symbol)["15m"]
        data[symbol] = (m15, load_multi_derivatives(lock, set_name, symbol, m15.index))

    rows = []
    for logic_id in [x.strip() for x in args.logics.split(",") if x.strip()]:
        needs = logic_id in NEEDS_DERIVATIVES
        runs = []
        for seed in range(-1, args.seeds):
            n_total, pnl_total = 0, 0.0
            for symbol, (m15, deriv) in data.items():
                frame = m15 if seed < 0 else jitter(m15, args.rel, seed * 1000 + hash(symbol) % 997)
                n, pnl = run_one(cfg, frame, logic_id, deriv if needs else None, start, end)
                n_total += n
                pnl_total += pnl
            ev = pnl_total / n_total if n_total else 0.0
            runs.append({"seed": "none" if seed < 0 else seed, "trades": n_total, "ev": ev})
            print(f"  {logic_id:16s} seed={runs[-1]['seed']!s:5s} n={n_total:4d} EV={ev:+.3f}", flush=True)

        clean = runs[0]
        jittered = runs[1:]
        evs = [r["ev"] for r in jittered]
        ns = [r["trades"] for r in jittered]
        row = {
            "logic_id": logic_id,
            "set": set_name,
            "rel": args.rel,
            "clean_trades": clean["trades"],
            "clean_ev": clean["ev"],
            "jitter_ev_min": min(evs),
            "jitter_ev_max": max(evs),
            "jitter_ev_mean": float(np.mean(evs)),
            "jitter_ev_std": float(np.std(evs)),
            "jitter_trades_min": min(ns),
            "jitter_trades_max": max(ns),
            "ev_sign_stable": all(e > 0 for e in evs) or all(e < 0 for e in evs),
            "runs": runs,
        }
        rows.append(row)
        print(
            f"{logic_id}: clean EV {clean['ev']:+.3f} n={clean['trades']}  "
            f"jitter EV {min(evs):+.3f}..{max(evs):+.3f} (sd {row['jitter_ev_std']:.3f}) "
            f"n {min(ns)}..{max(ns)}\n",
            flush=True,
        )

    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print("→", args.out)


if __name__ == "__main__":
    main()
