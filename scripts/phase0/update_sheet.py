"""Update phase0-verification-sheet.csv from B01 JSON results."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "docs/research/phase0-verification-sheet.csv"
RESULTS = ROOT / "data/phase0/b01_results.json"


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v:
            return ""
        return f"{v:.6f}"
    return str(v)


def main() -> None:
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    sample_period = payload["sample_period"]

    with SHEET.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

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
        extra = m.get("notes", "")
        if extra:
            row["notes"] = extra

    with SHEET.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {SHEET} with B01 results ({len(metrics)} metrics)")


if __name__ == "__main__":
    main()
