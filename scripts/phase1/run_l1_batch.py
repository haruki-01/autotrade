"""Run L1 exploration batches (P2-A/B/C/D)."""

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
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "l1"

BATCH_MODULES = {
    "P2-A": "scripts.phase1.p2a_hb_early",
    "P2-B": "scripts.phase1.p2b_hb_pull",
    "P2-C": "scripts.phase1.p2c_hbd_composite",
    "P2-D": "scripts.phase1.p2d_hc_session",
    "P2-E": "scripts.phase1.p2e_hc2_gap",
}


def run_batch(batch_id: str, df=None, *, skip_preflight: bool = False) -> dict:
    mod_name = BATCH_MODULES.get(batch_id.upper())
    if not mod_name:
        raise ValueError(f"Unknown L1 batch: {batch_id}")
    mod = importlib.import_module(mod_name)
    if df is None:
        df = load_or_fetch(SAMPLE_START, SAMPLE_END)
        print(f"Loaded {len(df)} bars")

    preflight_result = {"passed": True, "checks": []}
    if not skip_preflight:
        preflight_result = run_module_preflight(mod, df)
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


def run_all(df=None) -> dict:
    if df is None:
        df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    summaries = {}
    for bid in BATCH_MODULES:
        summaries[bid] = run_batch(bid, df=df)
    summary_path = OUT_DIR / "l1_exploration_summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"Wrote {summary_path}")
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Run L1 exploration batch")
    parser.add_argument("batch_id", nargs="?", default="ALL", help="P2-A, P2-B, P2-C, P2-D, P2-E, or ALL")
    args = parser.parse_args()
    if args.batch_id.upper() == "ALL":
        run_all()
    else:
        payload = run_batch(args.batch_id)
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
