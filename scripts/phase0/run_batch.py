"""Phase0 batch runner."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import date
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.research.preflight import batch_metadata
from scripts.phase0.update_sheet import update_sheet_from_json

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "phase0"

BATCH_MODULES = {
    "B01": "scripts.phase0.b01_metrics",
    "B02": "scripts.phase0.b02_metrics",
    "B03": "scripts.phase0.b03_metrics",
    "B04": "scripts.phase0.b04_metrics",
    "B05": "scripts.phase0.b05_metrics",
    "B06": "scripts.phase0.b06_metrics",
    "B07": "scripts.phase0.b07_metrics",
    "B08": "scripts.phase0.b08_metrics",
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
        **batch_metadata(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{batch_id.lower()}_results.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    update_sheet_from_json(out_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase0 verification batch")
    parser.add_argument("batch_id", help="Batch ID e.g. B02")
    args = parser.parse_args()
    payload = run_batch(args.batch_id)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
