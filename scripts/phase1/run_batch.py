"""Phase1 batch runner."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import date
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.phase1.update_sheet import update_sheet_from_json

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "phase1"

BATCH_MODULES = {
    "P1-A": "scripts.phase1.p1a_hd",
    "P1-B": "scripts.phase1.p1b_ha2",
    "P1-C": "scripts.phase1.p1c_composite",
    "P1-R": "scripts.phase1.p1r_grid",
    "P1-R2": "scripts.phase1.p1r2_exit_grid",
    "P1-HA": "scripts.phase1.p1ha_revert",
    "P1-N": "scripts.phase1.p1n_sensitivity",
}


def run_batch(batch_id: str, df=None) -> dict:
    mod_name = BATCH_MODULES.get(batch_id.upper())
    if not mod_name:
        raise ValueError(f"Unknown batch: {batch_id}")
    mod = importlib.import_module(mod_name)
    if df is None:
        df = load_or_fetch(SAMPLE_START, SAMPLE_END)
        print(f"Loaded {len(df)} bars")
    results = mod.compute(df)
    verdict_fn = getattr(mod, "batch_verdict", None)

    if batch_id.upper() in ("P1-R", "P1-R2"):
        metrics = results["metrics"]
        extra = {k: results[k] for k in ("grid", "gate2_combos", "gate1_combos", "tuning_split") if k in results}
    else:
        metrics = results
        extra = {}

    batch_verdict = verdict_fn(results if batch_id.upper() in ("P1-R", "P1-R2") else metrics) if verdict_fn else "unknown"
    payload = {
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "n_bars": len(df),
        "batch_id": batch_id.upper(),
        "batch_verdict": batch_verdict,
        "metrics": metrics,
        **extra,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = batch_id.lower().replace("-", "")
    if batch_id.upper() == "P1-N":
        from scripts.phase1.n_targets import write_n_targets_table

        write_n_targets_table()
    out_path = OUT_DIR / f"{slug}_results.json"
    if batch_id.upper() in ("P1-R", "P1-R2") and "grid" in payload:
        grid = payload.pop("grid")
        grid_path = OUT_DIR / "p1r_grid_full.json"
        grid_path.write_text(json.dumps({"grid": grid}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"Wrote {grid_path} ({len(grid)} combos)")
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {out_path}")
    update_sheet_from_json(out_path, batch_id)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase1 verification batch")
    parser.add_argument("batch_id", help="Batch ID e.g. P1-A")
    args = parser.parse_args()
    payload = run_batch(args.batch_id)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
