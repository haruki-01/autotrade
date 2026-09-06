"""Run Phase3 verification batches (P3-A/B/C)."""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import date
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.research.preflight import batch_metadata, run_module_preflight

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "phase3"

BATCH_MODULES = {
    "P3-A": "scripts.phase1.p3a_hf2",
    "P3-B": "scripts.phase1.p3b_hf3",
}


def _load_phase0_baseline(batch_id: str) -> dict | None:
    mapping = {"P3-A": "b08", "P3-B": "b09"}
    slug = mapping.get(batch_id.upper())
    if not slug:
        return None
    path = Path(__file__).resolve().parents[2] / "data" / "phase0" / f"{slug}_results.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("metrics")


def run_batch(batch_id: str, df=None, *, skip_preflight: bool = False) -> dict:
    mod_name = BATCH_MODULES.get(batch_id.upper())
    if not mod_name:
        raise ValueError(f"Unknown Phase3 batch: {batch_id}")
    mod = importlib.import_module(mod_name)
    if df is None:
        df = load_or_fetch(SAMPLE_START, SAMPLE_END)
        print(f"Loaded {len(df)} bars")

    preflight_result = {"passed": True, "checks": []}
    if not skip_preflight:
        baseline = _load_phase0_baseline(batch_id)
        preflight_result = run_module_preflight(mod, df, phase0_baseline=baseline)
        if not preflight_result.get("passed"):
            print(f"PREFLIGHT FAILED: {preflight_result}")
            payload = {
                "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
                "n_bars": len(df),
                "batch_id": batch_id.upper(),
                "batch_verdict": "preflight_fail",
                "preflight": preflight_result,
                **batch_metadata(),
            }
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            slug = batch_id.lower().replace("-", "")
            out_path = OUT_DIR / f"{slug}_results.json"
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
            return payload

    results = mod.compute(df)
    verdict_fn = getattr(mod, "batch_verdict", None)
    batch_verdict = verdict_fn(results) if verdict_fn else "unknown"
    payload = {
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "n_bars": len(df),
        "batch_id": batch_id.upper(),
        "batch_verdict": batch_verdict,
        "preflight": preflight_result,
        "metrics": results,
        **batch_metadata(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = batch_id.lower().replace("-", "")
    out_path = OUT_DIR / f"{slug}_results.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} — verdict={batch_verdict}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase3 verification batch")
    parser.add_argument("batch_id", help="P3-A, ...")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()
    payload = run_batch(args.batch_id, skip_preflight=args.skip_preflight)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
