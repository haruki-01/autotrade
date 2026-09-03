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
    batch_verdict = verdict_fn(results) if verdict_fn else "unknown"
    payload = {
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "n_bars": len(df),
        "batch_id": batch_id.upper(),
        "batch_verdict": batch_verdict,
        "metrics": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = batch_id.lower().replace("-", "")
    out_path = OUT_DIR / f"{slug}_results.json"
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
