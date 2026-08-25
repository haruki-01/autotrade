#!/usr/bin/env python3
"""Cross-period replication check for the EH-01..EH-10 100-cycle batch.

A single-period EV is not evidence. What matters is whether the base-vs-control
difference keeps its sign in both Set B (gate) and Set C (holdout). This script
merges the batch JSONs and writes the replication table used by the postmortem.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "eval" / "reports"
OUT = REPORTS / "20260823-edge-100-replication.md"

MIN_N = 30


def load(*names: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for name in names:
        for r in json.loads((REPORTS / name).read_text(encoding="utf-8")):
            if "error" in r:
                continue
            rows[r["logic_id"]] = r
    return rows


def main() -> int:
    b = load("20260823-edge-100-cycles-setB.json")
    c = load(
        "20260823-edge-100-cycles-setC.json",
        "20260823-edge-100-setC-blowups.json",
    )

    hyps = sorted({r["hypothesis_id"] for r in b.values()})
    lines = [
        "# EH-01〜EH-10 — 100サイクルの再現性チェック",
        "",
        "単一期間のEVは証拠にならない。**本命と対照のEV差が Set B と Set C で同じ符号か**を見る。",
        "",
        f"- Set B: 2024年（ゲート期間） / Set C: 2025-01〜2026-08（holdout）",
        f"- n<{MIN_N} は判定不能として扱う",
        "",
        "| 仮説 | 対照 | ΔEV(B) | ΔEV(C) | 符号 | 読み取り |",
        "|------|------|--------|--------|------|----------|",
    ]

    verdicts: dict[str, list[str]] = {}
    for h in hyps:
        base_id = next(
            (lid for lid, r in b.items() if r["hypothesis_id"] == h and lid.endswith("_base")),
            None,
        )
        ctrls = [lid for lid, r in b.items() if r["hypothesis_id"] == h and "_ctrl_" in lid]
        if base_id is None:
            continue
        for cid in ctrls:
            bb, bc = b.get(base_id), b.get(cid)
            cb, cc = c.get(base_id), c.get(cid)
            if not all([bb, bc, cb, cc]):
                lines.append(f"| {h} | `{cid}` | — | — | 判定不能 | 片方の期間でデータなし |")
                verdicts.setdefault(h, []).append("判定不能")
                continue
            db = bb["avg_trade_pnl"] - bc["avg_trade_pnl"]
            dc = cb["avg_trade_pnl"] - cc["avg_trade_pnl"]
            thin = min(bb["trades"], bc["trades"], cb["trades"], cc["trades"]) < MIN_N
            if thin:
                sign, note = "判定不能", "いずれかの期間で n<30"
            elif db > 0 and dc > 0:
                sign, note = "**+/+ 再現**", "対照より本命が良い（両期間）"
            elif db < 0 and dc < 0:
                sign, note = "−/− 逆再現", "対照のほうが良い（両期間）＝仮説と反対"
            else:
                sign, note = "不安定", "期間で符号が反転＝期間依存"
            lines.append(
                f"| {h} | `{cid}` | {db:+.3f} | {dc:+.3f} | {sign} | {note} |"
            )
            verdicts.setdefault(h, []).append(sign)

    lines += ["", "## 仮説ごとの結論", ""]
    lines += ["| 仮説 | 対照との比較 | 両期間PASS | 結論 |", "|------|--------------|-----------|------|"]
    for h in hyps:
        vs = verdicts.get(h, [])
        both = [
            lid
            for lid, r in b.items()
            if r["hypothesis_id"] == h and r["gate_pass"] and c.get(lid, {}).get("gate_pass")
        ]
        if vs and all(v.startswith("**+") for v in vs):
            mech = "再現"
        elif vs and any(v.startswith("−") for v in vs):
            mech = "逆（仮説と反対）"
        elif vs and all(v == "判定不能" for v in vs):
            mech = "判定不能（n不足）"
        else:
            mech = "不安定"
        if both:
            concl = f"保留（Set B/C 両PASS: {', '.join('`'+x+'`' for x in both)}）"
        elif mech == "再現":
            concl = "機構は再現。ただしゲート未達"
        elif mech.startswith("逆"):
            concl = "**棄却**（対照が上回る）"
        elif mech.startswith("判定不能"):
            concl = "**保留・要データ**（頻度不足で検証不能）"
        else:
            concl = "**棄却**（期間依存）"
        lines.append(f"| {h} | {mech} | {len(both)} | {concl} |")

    lines += ["", "## 口座を溶かした対照（DD>100%）", ""]
    blown = sorted(
        [r for r in c.values() if r["max_drawdown_pct"] > 100],
        key=lambda r: -r["max_drawdown_pct"],
    )
    if blown:
        lines.append("| logic | n | EV$ | DD% |")
        lines.append("|-------|---|-----|-----|")
        for r in blown:
            lines.append(
                f"| `{r['logic_id']}` | {r['trades']} | {r['avg_trade_pnl']:+.3f} | {r['max_drawdown_pct']:.1f} |"
            )
        lines.append("")
        lines.append(
            "いずれも「フィルタを外した対照」。無条件に撃つと Set C で証拠金を割り込む。"
        )
    else:
        lines.append("- なし")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
