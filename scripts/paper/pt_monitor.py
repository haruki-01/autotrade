"""PT-B paper trade monitoring — stop rules and benchmark checks."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

# Monitoring stop rules (paper-trade-spec §7)
CONSECUTIVE_LOSS_MONTHS_PAUSE = 3
N_BAND_LOW = 40
N_BAND_HIGH = 60


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def compare_p1r2c_reference(forward_summary: dict) -> dict:
    """Compare forward EV/P vs P1-R2C fixed-config Phase1 benchmarks."""
    payload = _load_json(ROOT / "data/phase1/p1r2c_results.json")
    if not payload:
        return {"p1r2c_available": False}

    metrics = payload.get("metrics", {})
    val = metrics.get("P1R2C-HD_VALIDATION", {})
    test = metrics.get("P1R2C-HD_TEST", {})
    oos_evs = [m.get("executed_ev") for m in (val, test) if m.get("executed_ev") is not None]
    oos_ps = [m.get("p") for m in (val, test) if m.get("p") is not None]
    phase1_ev = float(np.mean(oos_evs)) if oos_evs else np.nan
    phase1_p = float(np.mean(oos_ps)) if oos_ps else np.nan
    fwd_ev = forward_summary.get("ev") or 0
    fwd_p = forward_summary.get("p") or 0
    return {
        "p1r2c_available": True,
        "p1r2c_val_ev": val.get("executed_ev"),
        "p1r2c_val_p": val.get("p"),
        "p1r2c_test_ev": test.get("executed_ev"),
        "p1r2c_test_p": test.get("p"),
        "p1r2c_oos_avg_ev": phase1_ev,
        "p1r2c_oos_avg_p": phase1_p,
        "forward_ev": fwd_ev,
        "forward_p": fwd_p,
        "ev_vs_p1r2c": fwd_ev / phase1_ev if phase1_ev and phase1_ev != 0 else np.nan,
        "p_vs_p1r2c": fwd_p / phase1_p if phase1_p and phase1_p != 0 else np.nan,
        "p1r2c_ref_pass": (fwd_ev / phase1_ev >= 0.7) if phase1_ev and phase1_ev != 0 else False,
    }


def evaluate_stop_rules(monthly: list[dict], summary: dict) -> dict:
    """Apply paper monitoring stop/go rules."""
    alerts: list[str] = []
    status = "continue"

    if (summary.get("ev") or 0) <= 0:
        alerts.append("forward EV <= 0")
        status = "stop"

    consecutive_loss = 0
    max_consecutive_loss = 0
    for m in monthly:
        if (m.get("p") or 0) < 0:
            consecutive_loss += 1
            max_consecutive_loss = max(max_consecutive_loss, consecutive_loss)
        else:
            consecutive_loss = 0
    if max_consecutive_loss >= CONSECUTIVE_LOSS_MONTHS_PAUSE:
        alerts.append(f"{max_consecutive_loss} consecutive loss months")
        if status != "stop":
            status = "pause"

    n_violations = sum(
        1 for m in monthly if m.get("trades") and not (N_BAND_LOW <= m["trades"] <= N_BAND_HIGH)
    )
    if n_violations >= 2:
        alerts.append(f"N band violation in {n_violations} months")

    gate2_pass_months = sum(1 for m in monthly if m.get("gate2_pass"))
    gate2_pass_rate = gate2_pass_months / len(monthly) if monthly else 0.0

    if not summary.get("pt_gate1"):
        alerts.append("PT-Gate1 fail")
        status = "stop"

    return {
        "monitoring_status": status,
        "alerts": alerts,
        "max_consecutive_loss_months": max_consecutive_loss,
        "gate2_pass_months": gate2_pass_months,
        "gate2_pass_rate": round(gate2_pass_rate, 3),
        "months_tracked": len(monthly),
    }


def build_monitoring_block(
    forward_summary: dict,
    monthly: list[dict],
    split_breakdown: dict | None = None,
) -> dict:
    """Assemble PT-B monitoring section for results JSON."""
    p1r2c = compare_p1r2c_reference(forward_summary)
    stops = evaluate_stop_rules(monthly, forward_summary)
    return {
        **p1r2c,
        **stops,
        "split_breakdown": split_breakdown or {},
        "canonical_config": {
            "sl_pct": 0.005,
            "tp_pct": 0.01,
            "weekend_filter": True,
        },
    }
