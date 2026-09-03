"""Re-score Phase1 gate flags after Gate2 re-baseline (no backtest re-run)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.phase1.common import GATE2_P_TARGET, N_BAND_HIGH, N_BAND_LOW
from scripts.phase1.metrics import evaluate_gates

ROOT = Path(__file__).resolve().parents[2]
PHASE1_DATA = ROOT / "data" / "phase1"
OOS_SPLITS = ("OOS1", "OOS2")
SPLIT_KEYS = ("IS", "OOS1", "OOS2", "ALL")


def _verdict(gate1: bool, gate2: bool) -> str:
    if gate2:
        return "pass"
    if gate1:
        return "conditional"
    return "fail"


def _stats_from_block(block: dict) -> dict | None:
    ev = block.get("executed_ev")
    if ev is None:
        ev = block.get("ev")
    monthly_n = block.get("monthly_n")
    p = block.get("p")
    if ev is None and monthly_n is None and p is None:
        return None
    return {"ev": ev or 0, "monthly_n": monthly_n or 0, "p": p or 0}


def rescore_block(block: dict) -> bool:
    stats = _stats_from_block(block)
    if stats is None:
        return False
    gate1, gate2 = evaluate_gates(stats)
    block["gate1"] = gate1
    block["gate2"] = gate2
    if "verdict" in block or block.get("executed_ev") is not None or block.get("ev") is not None:
        block["verdict"] = _verdict(gate1, gate2)
    return True


def _oos_summary(splits: dict[str, dict]) -> dict:
    oos_ps = [splits[s]["p"] for s in OOS_SPLITS if s in splits and splits[s].get("p") is not None]
    oos_avg_p = sum(oos_ps) / len(oos_ps) if oos_ps else None
    gate1_both_oos = all(splits.get(s, {}).get("gate1") for s in OOS_SPLITS if s in splits)
    gate2_any_oos = any(splits.get(s, {}).get("gate2") for s in OOS_SPLITS if s in splits)
    gate2_both_oos = all(splits.get(s, {}).get("gate2") for s in OOS_SPLITS if s in splits)
    return {
        "oos_avg_p": oos_avg_p,
        "gate1_both_oos": gate1_both_oos,
        "gate2_any_oos": gate2_any_oos,
        "gate2_both_oos": gate2_both_oos,
    }


def rescore_p1r_metric(metric: dict) -> None:
    splits: dict[str, dict] = {}
    for key in SPLIT_KEYS:
        if key in metric and isinstance(metric[key], dict):
            rescore_block(metric[key])
            splits[key] = metric[key]
    if splits:
        summary = _oos_summary(splits)
        for k, v in summary.items():
            if v is not None:
                metric[k] = v


def rescore_grid_row(row: dict) -> None:
    for layer in ("theoretical", "executed"):
        if layer not in row:
            continue
        for split in SPLIT_KEYS:
            if split in row[layer]:
                rescore_block(row[layer][split])
    if "executed" in row:
        ex = row["executed"]
        summary = _oos_summary(ex)
        row.update(summary)


def rescore_standard_payload(payload: dict) -> str:
    metrics = payload.get("metrics", {})
    for _key, block in metrics.items():
        if isinstance(block, dict):
            rescore_block(block)

    gate2_any = any(m.get("gate2") for m in metrics.values() if isinstance(m, dict))
    gate1_any = any(m.get("gate1") for m in metrics.values() if isinstance(m, dict))
    if gate2_any:
        payload["batch_verdict"] = "pass"
    elif gate1_any:
        payload["batch_verdict"] = "conditional"
    else:
        payload["batch_verdict"] = "reject"
    return payload.get("batch_verdict", "")


def rescore_p1r_payload(payload: dict) -> str:
    metrics = payload.get("metrics", {})
    for key, metric in metrics.items():
        if not isinstance(metric, dict):
            continue
        if key.startswith("P1R-"):
            rescore_p1r_metric(metric)

    for row in payload.get("grid", []):
        rescore_grid_row(row)

    gate2_combos = [r for r in payload.get("grid", []) if r.get("gate2_any_oos")]
    gate1_combos = [r for r in payload.get("grid", []) if r.get("gate1_both_oos")]
    payload["gate2_combos"] = gate2_combos[:10]
    payload["gate1_combos"] = gate1_combos[:10]

    if "P1R-GRID-STATS" in metrics:
        metrics["P1R-GRID-STATS"]["gate2_any_count"] = len(gate2_combos)
        metrics["P1R-GRID-STATS"]["gate1_both_count"] = len(gate1_combos)

    best = metrics.get("P1R-BEST", {})
    baseline = metrics.get("P1R-BASELINE", {})
    if best.get("gate2_both_oos"):
        payload["batch_verdict"] = "promote"
    elif best.get("gate2_any_oos") or baseline.get("gate2_any_oos"):
        payload["batch_verdict"] = "conditional"
    elif best.get("gate1_both_oos") or baseline.get("gate1_both_oos"):
        payload["batch_verdict"] = "conditional"
    else:
        payload["batch_verdict"] = "reject"
    return payload.get("batch_verdict", "")


def rescore_file(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    batch_id = payload.get("batch_id", path.stem.upper())

    if batch_id == "P1-R" or path.name == "p1r_grid_full.json":
        verdict = rescore_p1r_payload(payload)
    else:
        verdict = rescore_standard_payload(payload)

    payload["gate2_target"] = GATE2_P_TARGET
    payload["rescore_note"] = f"Gate2 re-baseline: P*={GATE2_P_TARGET} JPY/month"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return verdict


def update_sheets() -> None:
    batches = [
        ("P1-A", PHASE1_DATA / "p1a_results.json"),
        ("P1-B", PHASE1_DATA / "p1b_results.json"),
        ("P1-C", PHASE1_DATA / "p1c_results.json"),
        ("P1-R", PHASE1_DATA / "p1r_results.json"),
    ]
    for batch_id, json_path in batches:
        if not json_path.exists():
            continue
        subprocess.run(
            [sys.executable, "-m", "scripts.phase1.update_sheet", batch_id, str(json_path)],
            check=True,
            cwd=ROOT,
        )


def main() -> None:
    targets = [
        PHASE1_DATA / "p1a_results.json",
        PHASE1_DATA / "p1b_results.json",
        PHASE1_DATA / "p1c_results.json",
        PHASE1_DATA / "p1r_results.json",
        PHASE1_DATA / "p1r_grid_full.json",
    ]
    for path in targets:
        if not path.exists():
            print(f"skip (missing): {path}")
            continue
        verdict = rescore_file(path)
        print(f"rescored {path.name}: batch_verdict={verdict}, gate2_target={GATE2_P_TARGET}")

    update_sheets()
    print("done")


if __name__ == "__main__":
    main()
