"""Forward paper-trade simulation with compounding bankroll."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.phase0.common import add_features
from scripts.phase1.backtest import run_backtest
from scripts.phase1.common import INITIAL_BANKROLL, POSITION_Q, filter_df_by_split
from scripts.phase1.signals.h_d_pull import generate_canonical_hd_signals

OOS_FORWARD = ("OOS1", "OOS2")
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "paper"


@dataclass
class PaperTradeRecord:
    entry_time: str
    exit_time: str
    entry_bar: int
    exit_bar: int
    exit_reason: str
    bankroll_at_entry: float
    position_q: float
    base_pnl: float
    scaled_pnl: float
    win: bool


def _scale_pnl(base_pnl: float, bankroll: float) -> tuple[float, float]:
    q = bankroll / 5
    scale = q / POSITION_Q
    return q, base_pnl * scale


def run_forward_paper(
    df: pd.DataFrame,
    initial_bankroll: float = INITIAL_BANKROLL,
    seed: int = 42,
) -> dict:
    """Run forward paper on OOS window with monthly compounding."""
    parts = []
    for split in OOS_FORWARD:
        parts.append(filter_df_by_split(df, split))
    forward_df = pd.concat(parts, ignore_index=True)
    forward_df = add_features(forward_df)

    sigs = generate_canonical_hd_signals(forward_df)
    trades = run_backtest(forward_df, sigs, apply_execution=True, seed=seed)

    bankroll = float(initial_bankroll)
    records: list[PaperTradeRecord] = []
    for t in trades:
        if not t.filled:
            continue
        entry_time = forward_df["open_time"].iloc[t.signal.bar_idx]
        exit_time = forward_df["open_time"].iloc[t.exit_bar_idx]
        q, scaled = _scale_pnl(t.executed_pnl, bankroll)
        records.append(
            PaperTradeRecord(
                entry_time=str(entry_time),
                exit_time=str(exit_time),
                entry_bar=t.signal.bar_idx,
                exit_bar=t.exit_bar_idx,
                exit_reason=t.exit_reason,
                bankroll_at_entry=bankroll,
                position_q=q,
                base_pnl=t.executed_pnl,
                scaled_pnl=scaled,
                win=bool(scaled > 0),
            )
        )
        bankroll += scaled

    monthly_buckets: dict[str, list[float]] = {}
    for r in records:
        mk = str(pd.Timestamp(r.exit_time).to_period("M"))
        monthly_buckets.setdefault(mk, []).append(r.scaled_pnl)

    sorted_months = sorted(monthly_buckets.keys())
    b = float(initial_bankroll)
    monthly_summary = []
    for mk in sorted_months:
        pnls_m = monthly_buckets[mk]
        n = len(pnls_m)
        wins = sum(1 for p in pnls_m if p > 0)
        ev = float(np.mean(pnls_m))
        p = sum(pnls_m)
        gate2_target = b * 0.05
        monthly_summary.append(
            {
                "month": mk,
                "bankroll_start": b,
                "trades": n,
                "w": wins / n if n else np.nan,
                "ev": ev,
                "p": p,
                "gate2_target": gate2_target,
                "gate2_pass": bool(p >= gate2_target),
                "bankroll_end": b + p,
            }
        )
        b += p

    pnls = [r.scaled_pnl for r in records]
    months_span = max(len(sorted_months), 1)
    n_total = len(pnls)
    ev = float(np.mean(pnls)) if pnls else 0.0
    monthly_n = n_total / months_span
    p_monthly = ev * monthly_n

    equity = np.cumsum(pnls) if pnls else np.array([0.0])
    peak = np.maximum.accumulate(equity) if len(equity) else np.array([0.0])
    max_dd = float((peak - equity).max()) if len(equity) else 0.0

    pt_gate1 = ev > 0 and 40 <= monthly_n <= 60
    pt_gate2 = p_monthly >= initial_bankroll * 0.05

    return {
        "records": records,
        "summary": {
            "n": n_total,
            "w": sum(1 for p in pnls if p > 0) / n_total if n_total else np.nan,
            "ev": ev,
            "monthly_n": monthly_n,
            "p": p_monthly,
            "max_dd": max_dd,
            "initial_bankroll": initial_bankroll,
            "final_bankroll": b,
            "total_return_pct": (b - initial_bankroll) / initial_bankroll * 100 if initial_bankroll else 0,
            "pt_gate1": pt_gate1,
            "pt_gate2": pt_gate2,
        },
        "monthly": monthly_summary,
    }


def compare_phase1_reference(p1c_path: Path, forward_summary: dict) -> dict:
    if not p1c_path.exists():
        return {"degradation": np.nan, "phase1_ev": np.nan}
    payload = json.loads(p1c_path.read_text())
    oos_evs = []
    for split in OOS_FORWARD:
        m = payload.get("metrics", {}).get(f"P1-COMPOSITE_{split}", {})
        if m.get("executed_ev") is not None:
            oos_evs.append(m["executed_ev"])
    phase1_ev = float(np.mean(oos_evs)) if oos_evs else np.nan
    fwd_ev = forward_summary.get("ev") or 0
    deg = fwd_ev / phase1_ev if phase1_ev and phase1_ev != 0 else np.nan
    return {
        "phase1_oos_avg_ev": phase1_ev,
        "forward_ev": fwd_ev,
        "degradation": deg,
        "pt_ref_pass": deg >= 0.7 if not np.isnan(deg) else False,
    }


def _load_v1_research_gate() -> dict:
    v1_path = Path(__file__).resolve().parents[2] / "data" / "validation" / "v1_all_results.json"
    if not v1_path.exists():
        return {"v1_research_gate_hd": None}
    payload = json.loads(v1_path.read_text())
    for r in payload.get("results", []):
        if r.get("strategy") == "hd":
            return {
                "v1_research_gate_hd": r.get("research_gate", {}).get("pass"),
                "v1_forward_ev": r.get("stats", {}).get("ev"),
            }
    return {"v1_research_gate_hd": None}


def compute(batch_id: str = "PT-A") -> dict:
    from scripts.phase0.common import load_or_fetch

    df = load_or_fetch(date(2024, 1, 1), date(2026, 8, 31))
    result = run_forward_paper(df)
    ref = compare_phase1_reference(
        Path(__file__).resolve().parents[2] / "data" / "phase1" / "p1c_results.json",
        result["summary"],
    )
    summary = {**result["summary"], **ref}
    if batch_id.upper() == "PT-B":
        summary.update(_load_v1_research_gate())
        summary["notes"] = "PT-B: forward monitoring post V1 Research Gate pass"
    verdict = "pass" if summary.get("pt_gate2") else ("conditional" if summary.get("pt_gate1") else "fail")
    if summary.get("pt_ref_pass") is False and verdict == "pass":
        verdict = "conditional"
    metric_id = f"{batch_id.upper()}-FORWARD"
    return {
        "metrics": {metric_id: {**summary, "verdict": verdict}},
        "records": result["records"],
        "monthly": result["monthly"],
    }


def batch_verdict(results: dict) -> str:
    for m in results.get("metrics", {}).values():
        if m.get("pt_gate2"):
            return "promote"
        if m.get("pt_gate1"):
            return "conditional"
    return "reject"


def save_results(payload: dict, batch_id: str = "PT-A", out_dir: Path | None = None) -> Path:
    out_dir = out_dir or DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = batch_id.lower().replace("-", "_")
    records = payload.pop("records", [])
    trades_path = out_dir / f"{slug}_trades.jsonl"
    with trades_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    out_path = out_dir / f"{slug}_results.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return out_path
