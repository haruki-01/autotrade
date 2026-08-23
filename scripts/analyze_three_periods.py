"""Cross-check a batch of logics over three evaluation periods.

Set B was used for exploration and Set C has now been looked at repeatedly, so
a variant surviving both is no longer strong evidence. Set A (2023) has never
been touched by these hypotheses, which makes it the honest tiebreaker.

Usage:
    python scripts/analyze_three_periods.py \
        --a eval/reports/<tag>-setA.json \
        --b eval/reports/<tag>-setB.json \
        --c eval/reports/<tag>-setC.json \
        --out eval/reports/<tag>-three-periods.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["runs"] if isinstance(payload, dict) else payload
    return {r["logic_id"]: r for r in rows}


def ev(row: dict) -> float:
    return float(row["avg_trade_pnl"])


def n(row: dict) -> int:
    return int(row["trades"])


def dd(row: dict) -> float:
    return float(row["max_drawdown_pct"])


def ret(row: dict) -> float:
    return float(row["total_return_pct"])


def verdict(rows: list[dict]) -> str:
    passes = sum(1 for r in rows if r["gate_pass"])
    signs = [ev(r) > 0 for r in rows]
    if passes == 3:
        return "**3期間PASS**"
    if all(signs):
        return "3期間プラス（ゲートは未通過あり）"
    if not any(signs):
        return "3期間マイナス"
    return "期間依存"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--c", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="3期間クロスチェック")
    args = ap.parse_args()

    a, b, c = load(Path(args.a)), load(Path(args.b)), load(Path(args.c))
    shared = [lid for lid in b if lid in a and lid in c]

    lines: list[str] = [
        f"# {args.title}",
        "",
        "Set B は探索に使い、Set C も複数フェーズで参照済み。"
        "Set A (2023) はこれらの仮説で一度も見ていないため、ここでの符号を最終判断に使う。",
        "",
        "| logic | EV(A) | n(A) | EV(B) | n(B) | EV(C) | n(C) | 最大DD(A/B/C) | 判定 |",
        "|-------|-------|------|-------|------|-------|------|----------------|------|",
    ]

    scored = []
    for lid in shared:
        ra, rb, rc = a[lid], b[lid], c[lid]
        scored.append((sum(1 for r in (ra, rb, rc) if r["gate_pass"]), min(ev(ra), ev(rb), ev(rc)), lid))
    scored.sort(reverse=True)

    survivors: list[str] = []
    for _, _, lid in scored:
        ra, rb, rc = a[lid], b[lid], c[lid]
        v = verdict([ra, rb, rc])
        if v == "**3期間PASS**":
            survivors.append(lid)
        lines.append(
            f"| `{lid}` | {ev(ra):+.3f} | {n(ra)} | {ev(rb):+.3f} | {n(rb)} "
            f"| {ev(rc):+.3f} | {n(rc)} "
            f"| {dd(ra):.1f}/{dd(rb):.1f}/{dd(rc):.1f}% | {v} |"
        )

    families = sorted({lid.split("_")[0] for lid in shared})
    lines += ["", "## 系統別の要約", ""]
    for fam in families:
        ids = [lid for lid in shared if lid.startswith(fam)]
        pa = sum(1 for lid in ids if a[lid]["gate_pass"])
        pb = sum(1 for lid in ids if b[lid]["gate_pass"])
        pc = sum(1 for lid in ids if c[lid]["gate_pass"])
        pos_a = sum(1 for lid in ids if ev(a[lid]) > 0)
        lines.append(
            f"- `{fam}`: PASS A={pa}/{len(ids)} B={pb}/{len(ids)} C={pc}/{len(ids)}、"
            f"Set A で EV>0 は {pos_a}/{len(ids)} 本"
        )

    lines += ["", "## 3期間PASS", ""]
    if survivors:
        for lid in survivors:
            ra, rb, rc = a[lid], b[lid], c[lid]
            lines.append(
                f"- `{lid}` — A {ev(ra):+.3f}/{n(ra)}本、B {ev(rb):+.3f}/{n(rb)}本、"
                f"C {ev(rc):+.3f}/{n(rc)}本"
            )
    else:
        lines.append("- なし")

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
