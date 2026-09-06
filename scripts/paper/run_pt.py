"""Paper trade batch runner."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.paper.forward_engine import batch_verdict, compute, save_results
from scripts.research.preflight import batch_metadata

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "paper"


def run_pt(batch_id: str = "PT-A", df=None) -> dict:
    batch_id = batch_id.upper()
    if df is None:
        df = load_or_fetch(SAMPLE_START, SAMPLE_END)
        print(f"Loaded {len(df)} bars")
    results = compute(batch_id=batch_id)
    verdict = batch_verdict(results)
    payload = {
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "forward_window": "OOS1+OOS2 (2025-07-01..2026-08-31)",
        "n_bars": len(df),
        "batch_id": batch_id,
        "batch_verdict": verdict,
        **batch_metadata(),
        **results,
    }
    out_path = save_results(payload, batch_id=batch_id, out_dir=OUT_DIR)
    print(f"Wrote {out_path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paper trade verification")
    parser.add_argument("batch_id", nargs="?", default="PT-A", help="PT-A or PT-B")
    args = parser.parse_args()
    payload = run_pt(args.batch_id)
    print(json.dumps(payload["metrics"], indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
