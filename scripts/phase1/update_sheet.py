"""Update phase1-verification-sheet.csv from batch JSON."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "docs/research/phase1-verification-sheet.csv"

METRIC_MAP = {
    "P1-A": {
        "P1-HD-PULL_IS": ("P1-HD-PULL", "IS"),
        "P1-HD-PULL_OOS1": ("P1-HD-PULL", "OOS1"),
        "P1-HD-PULL_OOS2": ("P1-HD-PULL", "OOS2"),
        "P1-HD-RAW-CTRL": ("P1-HD-RAW-CTRL", "IS"),
        "P1-HD-RANDOM": ("P1-HD-RANDOM", "ALL"),
    },
    "P1-B": {
        "P1-HA2-CONT_IS": ("P1-HA2-CONT", "IS"),
        "P1-HA2-CONT_OOS1": ("P1-HA2-CONT", "OOS1"),
        "P1-HA2-CONT_OOS2": ("P1-HA2-CONT", "OOS2"),
        "P1-HA-REVERT-CTRL": ("P1-HA-REVERT-CTRL", "IS"),
        "P1-HA2-RANDOM": ("P1-HA2-RANDOM", "ALL"),
    },
    "P1-C": {
        "P1-COMPOSITE_IS": ("P1-COMPOSITE", "IS"),
        "P1-COMPOSITE_OOS1": ("P1-COMPOSITE", "OOS1"),
        "P1-COMPOSITE_OOS2": ("P1-COMPOSITE", "OOS2"),
    },
    "P1-R": {
        ("P1R-BEST", "IS"): ("P1R-BEST", "IS"),
        ("P1R-BEST", "OOS1"): ("P1R-BEST", "OOS1"),
        ("P1R-BEST", "OOS2"): ("P1R-BEST", "OOS2"),
        ("P1R-BASELINE", "IS"): ("P1R-BASELINE", "IS"),
        ("P1R-BASELINE", "OOS1"): ("P1R-BASELINE", "OOS1"),
        ("P1R-BASELINE", "OOS2"): ("P1R-BASELINE", "OOS2"),
    },
}

P1N_ROW_TEMPLATE = {
    "batch_id": "P1-N",
    "purpose": "N感度（cooldown調整）",
    "decision_question": "各N帯でGate1/2に届くか？",
    "hypothesis_id": "H-D",
    "split": "OOS",
}


def _append_p1n_rows(rows: list[dict], fieldnames: list[str], payload: dict) -> int:
    metrics = payload["metrics"]
    added = 0
    existing = {(r["metric_id"], r.get("split")) for r in rows}
    for key, m in metrics.items():
        if key in existing:
            continue
        row = {fn: "" for fn in fieldnames}
        row.update(P1N_ROW_TEMPLATE)
        row["metric_id"] = key
        row["executed_ev"] = fmt(m.get("oos_avg_ev"))
        row["w"] = fmt(m.get("oos_avg_w"))
        row["monthly_n"] = fmt(m.get("oos_avg_n"))
        row["p"] = fmt(m.get("oos_avg_p"))
        row["fee_breakeven_w"] = fmt(m.get("fee_breakeven_w"))
        row["gate1"] = fmt(m.get("gate1"))
        row["gate2"] = fmt(m.get("gate2"))
        row["verdict"] = m.get("verdict", "")
        row["sample_period"] = payload.get("sample_period", "")
        row["notes"] = f"cooldown={m.get('cooldown')}, w_star={m.get('w_star_gate2')}"
        rows.append(row)
        added += 1
    return added


def fmt(v) -> str:
    if v is None or v is True or v is False:
        return str(v) if isinstance(v, bool) else ""
    if isinstance(v, float):
        if v != v:
            return ""
        return f"{v:.4f}"
    return str(v)


def update_sheet_from_json(results_path: Path, batch_id: str) -> None:
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    mapping = METRIC_MAP.get(batch_id.upper(), {})

    with SHEET.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    if batch_id.upper() == "P1-N":
        updated = _append_p1n_rows(rows, fieldnames, payload)
    elif batch_id.upper() == "P1-R":
        for row in rows:
            mid, split = row["metric_id"], row["split"]
            key = (mid, split)
            if key not in mapping:
                continue
            src = metrics.get(mid, {})
            if split not in src:
                continue
            m = src[split]
            for col in ("executed_ev", "n", "w", "monthly_n", "p", "max_dd", "fee_breakeven_w"):
                if col in m:
                    val = m[col]
                    if col == "executed_ev":
                        row["executed_ev"] = fmt(val)
                    else:
                        row[col] = fmt(val)
            row["gate1"] = fmt(m.get("gate1"))
            row["gate2"] = fmt(m.get("gate2"))
            row["verdict"] = "pass" if m.get("gate2") else ("conditional" if m.get("gate1") else "fail")
            row["sample_period"] = payload.get("sample_period", "")
            if src.get("params"):
                row["notes"] = str(src["params"])
            updated += 1
    else:
        for row in rows:
            for json_key, (mid, split) in mapping.items():
                if row["metric_id"] != mid or row["split"] != split:
                    continue
                if json_key not in metrics:
                    continue
                m = metrics[json_key]
                for col in ("theoretical_ev", "executed_ev", "degradation", "n", "w", "monthly_n", "p", "max_dd", "random_w", "fee_breakeven_w"):
                    if col in m:
                        row[col] = fmt(m[col])
                row["gate1"] = fmt(m.get("gate1"))
                row["gate2"] = fmt(m.get("gate2"))
                row["verdict"] = m.get("verdict", "")
                row["sample_period"] = payload.get("sample_period", "")
                if m.get("notes"):
                    row["notes"] = m["notes"]
                updated += 1

    with SHEET.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Updated {updated} rows in {SHEET}")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python3 -m scripts.phase1.update_sheet P1-A data/phase1/p1a_results.json")
        sys.exit(1)
    update_sheet_from_json(Path(sys.argv[2]), sys.argv[1])


if __name__ == "__main__":
    main()
