"""V1 validation batch + B10 MFE runner."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import filter_df_by_split
from scripts.phase1.p3bnr_eval import HF3NRConfig, _signal_kwargs
from scripts.phase1.signals.h_d_pull import generate_canonical_hd_signals
from scripts.phase1.signals.h_f3_range import generate_hf3_revert_signals
from scripts.phase1.validation.monte_carlo import run_monte_carlo, run_trade_shuffle
from scripts.phase1.validation.research_gate import evaluate_research_gate
from scripts.phase1.validation.risk_metrics import extended_summarize
from scripts.phase1.validation.robustness import run_robustness
from scripts.phase1.validation.walk_forward import run_walk_forward

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "validation"


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def _hd_signal_fn(sub):
    return generate_canonical_hd_signals(sub)


def _hf3_signal_fn(cfg: HF3NRConfig):
    sig_kw = _signal_kwargs(cfg)

    def fn(sub):
        return generate_hf3_revert_signals(sub, **sig_kw)

    return fn


def run_v1(df, strategy: str, hf3_config: HF3NRConfig | None = None) -> dict:
    hf3_config = hf3_config or HF3NRConfig(cooldown=4, range_quantile=0.40, atr_touch_mult=0.20)

    if strategy == "hd":
        signal_fn = _hd_signal_fn
        label = "H-D+M4"
    elif strategy == "hf3":
        signal_fn = _hf3_signal_fn(hf3_config)
        label = f"H-F3 ({hf3_config.label()})"
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    val_df = filter_df_by_split(df, "VALIDATION")
    sigs = signal_fn(val_df)
    trades = run_backtest(val_df, sigs, apply_execution=True)
    stats = extended_summarize(trades, val_df, "executed_pnl")
    stats["executed_ev"] = stats.get("ev")
    stats["label"] = label

    pnls = [t.executed_pnl for t in trades if t.filled]
    wf = run_walk_forward(df, signal_fn, apply_execution=True)
    mc = run_monte_carlo(pnls)
    shuffle = run_trade_shuffle(pnls)
    robust = run_robustness(val_df, signal_fn)
    rg = evaluate_research_gate(stats, wf, mc, robust)

    gate1 = stats.get("ev", 0) > 0 and 40 <= (stats.get("monthly_n") or 0) <= 60
    gate2 = (stats.get("p") or 0) >= 2500

    return {
        "batch_id": "V1",
        "strategy": strategy,
        "label": label,
        "split": "VALIDATION",
        "stats": stats,
        "walk_forward": wf,
        "monte_carlo": mc,
        "trade_shuffle": shuffle,
        "robustness": robust,
        "research_gate": rg,
        "gate1": gate1,
        "gate2": gate2,
        "batch_verdict": "promote" if rg["pass"] and gate2 else ("conditional" if rg["pass"] or gate1 else "reject"),
    }


def run_b10(df, strategy: str = "all") -> dict:
    from scripts.phase0.b10_mfe_metrics import compute, batch_verdict

    hf3_cfg = HF3NRConfig(cooldown=4, range_quantile=0.40, atr_touch_mult=0.20)
    results = compute(df, strategy=strategy, hf3_config=hf3_cfg)
    return {
        "batch_id": "B10",
        "strategy_filter": strategy,
        "results": results,
        "batch_verdict": batch_verdict(results),
        "git_commit": _git_commit(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Run validation batches V1 / B10")
    parser.add_argument("batch", choices=["V1", "B10"])
    parser.add_argument("--strategy", choices=["hd", "hf3", "all"], default="hd")
    parser.add_argument("--hf3-config", default="cd4_q40_at20", help="HF3NR config label hint")
    args = parser.parse_args()

    df = load_or_fetch(date(2024, 1, 1), date(2026, 8, 31))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.batch == "V1":
        if args.strategy == "all":
            outputs = [run_v1(df, "hd"), run_v1(df, "hf3")]
            out_path = OUT_DIR / "v1_all_results.json"
            payload = {
                "batch_id": "V1",
                "results": outputs,
                "git_commit": _git_commit(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            payload = run_v1(df, args.strategy)
            payload["git_commit"] = _git_commit()
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
            out_path = OUT_DIR / f"v1_{args.strategy}_results.json"
    else:
        payload = run_b10(df, args.strategy)
        out_path = OUT_DIR / f"b10_{args.strategy}_results.json"

    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Verdict: {payload.get('batch_verdict') or payload.get('results', [{}])[0].get('batch_verdict', 'n/a')}")


if __name__ == "__main__":
    main()
