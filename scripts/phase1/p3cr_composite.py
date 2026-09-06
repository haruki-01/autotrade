"""P3-C-R: H-D zone filter + H-F3 with strict zone lookback=24."""

from __future__ import annotations

from scripts.phase1 import p3c_composite as p3c

ZONE_LOOKBACK = 24


def compute(df) -> dict[str, dict]:
    metrics = {}
    for split in ("IS", "OOS1", "OOS2"):
        metrics[f"P3CR-COMPOSITE_{split}"] = p3c._run_split(df, split, zone_lookback=ZONE_LOOKBACK)

    p3c_ref = p3c.compute(df)
    val = metrics.get("P3CR-COMPOSITE_OOS1", {})
    ref_val = p3c_ref.get("P3C-COMPOSITE_OOS1", {})
    metrics["P3C-REF-OOS1"] = ref_val
    metrics["P3CR-META"] = {
        "zone_lookback": ZONE_LOOKBACK,
        "validation_filter_ratio": val.get("filter_ratio"),
        "validation_n": val.get("n"),
        "validation_p": val.get("p"),
        "p3c_validation_p": ref_val.get("p"),
        "validation_executed_ev": val.get("executed_ev"),
    }
    return metrics


def batch_verdict(results: dict[str, dict]) -> str:
    val = results.get("P3CR-COMPOSITE_OOS1", {})
    ref = results.get("P3C-REF-OOS1", {})
    if val.get("gate2"):
        return "promote"
    if val.get("gate1"):
        return "conditional"
    val_p = val.get("p") or 0
    ref_p = ref.get("p") or 0
    val_ev = val.get("executed_ev") or 0
    ref_ev = ref.get("executed_ev") or 0
    if val_p > ref_p and val_ev > ref_ev:
        return "conditional"
    if val_ev > 0:
        return "conditional"
    return "reject"
