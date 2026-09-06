"""Gate2 what-if rescore report (no backtest re-run)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "research" / "gate2_rescore_3pct.json"

OOS_MARKERS = ("OOS1", "OOS2", "VALIDATION", "TEST", "OOS-FWD", "FORWARD", "OOS avg")


def _scan(obj, file: str, ctx: str = "", rows: list | None = None) -> list:
    if rows is None:
        rows = []
    if isinstance(obj, dict):
        p = obj.get("p") or obj.get("oos_avg_p") or obj.get("oos_executed_p")
        if p is not None and isinstance(p, (int, float)) and not isinstance(p, bool) and p > 200:
            rows.append(
                {
                    "file": file,
                    "metric": ctx.split(".")[-1] if ctx else "",
                    "context": ctx[-80:],
                    "split": obj.get("split", ""),
                    "p": round(float(p), 2),
                    "executed_ev": obj.get("executed_ev") or obj.get("ev") or obj.get("oos_executed_ev"),
                    "monthly_n": obj.get("monthly_n") or obj.get("oos_executed_n"),
                    "gate1": obj.get("gate1"),
                    "gate2_at_5pct": float(p) >= 2500,
                    "gate2_at_3pct": float(p) >= 1500,
                    "pct_of_5pct_target": round(float(p) / 2500, 3),
                    "pct_of_3pct_target": round(float(p) / 1500, 3),
                    "is_oos": any(m in ctx or str(obj.get("split", "")) for m in OOS_MARKERS),
                }
            )
        for k, v in obj.items():
            _scan(v, file, f"{ctx}.{k}" if ctx else k, rows)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan(v, file, f"{ctx}[{i}]", rows)
    return rows


def build_report(old_pct: float = 0.05, new_pct: float = 0.03, br: int = 50_000) -> dict:
    old_target = int(br * old_pct)
    new_target = int(br * new_pct)
    rows = []
    for fp in sorted((ROOT / "data").rglob("*.json")):
        if "loop/iter_" in str(fp) or fp.name == OUT.name:
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows.extend(_scan(data, fp.relative_to(ROOT).as_posix()))

    seen: set[tuple] = set()
    uniq = []
    for r in sorted(rows, key=lambda x: -x["p"]):
        key = (r["file"], r["context"], r["p"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    new_pass = [r for r in uniq if r["gate2_at_3pct"]]
    new_pass_oos_g1 = [
        r for r in uniq if r["gate2_at_3pct"] and r["is_oos"] and r.get("gate1") is True
    ]
    near_oos_g1 = [
        r
        for r in uniq
        if r["is_oos"] and r.get("gate1") is True and not r["gate2_at_3pct"] and r["p"] >= 900
    ]
    near_oos_g1.sort(key=lambda x: -x["p"])

    return {
        "gate2_old": {"pct": old_pct, "p_target_jpy": old_target},
        "gate2_new": {"pct": new_pct, "p_target_jpy": new_target},
        "ev_star_at_n50": {"old": old_target / 50, "new": new_target / 50},
        "summary": {
            "total_metrics_scanned": len(uniq),
            "gate2_pass_at_5pct": sum(1 for r in uniq if r["gate2_at_5pct"]),
            "gate2_pass_at_3pct": len(new_pass),
            "gate2_pass_at_3pct_oos_and_gate1": len(new_pass_oos_g1),
        },
        "gate2_pass_at_3pct": new_pass[:20],
        "near_miss_oos_gate1": near_oos_g1[:15],
        "recommendation": (
            "Gate2@3%でも OOS+Gate1 pass 候補はゼロ。"
            "L0変更は進捗指標の現実化として有効だが promote 候補は未出。"
            "最良: P1-R2C VALIDATION P≈¥1,031（新目標の69%）。"
        ),
    }


def main() -> None:
    report = build_report()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
