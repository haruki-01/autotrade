"""Configurable research loop template (verify → update → verify)."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from scripts.phase0.common import load_or_fetch
from scripts.research.preflight import batch_metadata

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "data" / "research" / "p3nr_config.json"

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)


def run_loop(config_path: Path) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    batch_id = cfg.get("batch_id", "P3-NR")
    max_iter = int(cfg.get("max_iterations", 10))
    stop_no_improve = int(cfg.get("stop_if", {}).get("no_improvement_for", 3))

    df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    mod_name = cfg.get("module", "scripts.phase1.p3a_hf2")
    import importlib

    mod = importlib.import_module(mod_name)
    evaluate_fn = getattr(mod, "evaluate_config", None)
    if evaluate_fn is None:
        # fallback: run full compute once
        results = mod.compute(df)
        payload = {
            "batch_id": batch_id,
            "iterations": 1,
            "best": results,
            "history": [],
            **batch_metadata(),
        }
        out = ROOT / "data" / "research" / f"{batch_id.lower()}_loop_summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        return payload

    history: list[dict] = []
    best: dict | None = None
    stale = 0

    for i in range(1, max_iter + 1):
        configs = cfg.get("iter_configs", {}).get(str(i), cfg.get("initial_configs", []))
        iter_results = []
        for c in configs:
            r = evaluate_fn(df, c)
            iter_results.append(r)
            if best is None or (r.get("executed_p") or 0) > (best.get("executed_p") or 0):
                if best and (r.get("executed_p") or 0) <= (best.get("executed_p") or 0):
                    stale += 1
                else:
                    stale = 0
                best = r

        history.append({"iter": i, "results": iter_results, "best_p": best.get("executed_p") if best else None})
        if best and best.get("gate2"):
            break
        if stale >= stop_no_improve:
            break

    payload = {
        "batch_id": batch_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "iterations": len(history),
        "best": best,
        "history": history,
        **batch_metadata(),
    }
    out = ROOT / "data" / "research" / f"{batch_id.lower()}_loop_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run configurable research loop")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()
    run_loop(Path(args.config))


if __name__ == "__main__":
    main()
