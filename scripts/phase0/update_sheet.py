"""Update phase0-verification-sheet.csv from batch JSON results."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "docs/research/phase0-verification-sheet.csv"


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v:
            return ""
        return f"{v:.6f}"
    return str(v)


def update_sheet_from_json(results_path: Path) -> None:
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    sample_period = payload["sample_period"]

    with SHEET.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    for row in rows:
        mid = row["metric_id"]
        if mid not in metrics:
            continue
        m = metrics[mid]
        row["status"] = "done"
        row["n"] = fmt(m.get("n"))
        row["hit_rate"] = fmt(m.get("hit_rate"))
        row["mean_edge"] = fmt(m.get("mean_edge"))
        row["median_edge"] = fmt(m.get("median_edge"))
        row["p25"] = fmt(m.get("p25"))
        row["p75"] = fmt(m.get("p75"))
        row["mean_abs_move"] = fmt(m.get("mean_abs_move"))
        row["vs_baseline"] = fmt(m.get("vs_baseline"))
        row["verdict"] = m.get("verdict", "")
        row["sample_period"] = sample_period
        if m.get("notes"):
            row["notes"] = m["notes"]
        updated += 1

    with SHEET.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {updated} rows in {SHEET}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 -m scripts.phase0.update_sheet data/phase0/b02_results.json")
        sys.exit(1)
    update_sheet_from_json(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
