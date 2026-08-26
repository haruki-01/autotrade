#!/usr/bin/env python3
"""Which knobs actually helped — judged on both periods, not one.

For each refinement pack, every variant is compared against its own base line in
Set B and Set C. Only knobs that move EV the same way in both periods are worth
carrying forward; anything that flips sign is period-dependent noise.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "eval" / "reports"
OUT = REPORTS / "20260823-edge-refine-consistency.md"

BASES = {"EH-01R": "eh01r_base", "EH-07R": "eh07r_base", "EH-02R": "eh02r_base"}
MIN_N = 30


def load(name: str) -> dict[str, dict]:
    return {
        r["logic_id"]: r
        for r in json.loads((REPORTS / name).read_text(encoding="utf-8"))
        if "error" not in r
    }


def main() -> int:
    b = load("20260823-edge-refine-setB.json")
    c = load("20260823-edge-refine-setC.json")

    lines = [
        "# EH-01R / EH-07R / EH-02R — 改良ノブの一貫性",
        "",
        "各ノブを **自分の基準線（base）との差** で評価する。Set B と Set C で",
        "同じ向きに動いたノブだけが持ち越す価値がある。符号が反転したものは期間依存。",
        "",
        f"- n<{MIN_N} は判定不能",
        "- ΔEV は base に対する1トレードあたりの改善（＋が良い）",
        "",
    ]

    for hyp, base_id in BASES.items():
        bb, cb = b.get(base_id), c.get(base_id)
        if not bb or not cb:
            continue
        lines += [
            f"## {hyp}",
            "",
            f"基準線 `{base_id}`: Set B n={bb['trades']} EV={bb['avg_trade_pnl']:+.3f} / "
            f"Set C n={cb['trades']} EV={cb['avg_trade_pnl']:+.3f}",
            "",
            "| ノブ | ΔEV(B) | ΔEV(C) | 判定 |",
            "|------|--------|--------|------|",
        ]
        prefix = base_id.rsplit("_", 1)[0] + "_"
        rows = []
        for lid, rb in b.items():
            if not lid.startswith(prefix) or lid == base_id:
                continue
            rc = c.get(lid)
            if rc is None:
                continue
            if min(rb["trades"], rc["trades"]) < MIN_N:
                verdict, db, dc = "判定不能", None, None
            else:
                db = rb["avg_trade_pnl"] - bb["avg_trade_pnl"]
                dc = rc["avg_trade_pnl"] - cb["avg_trade_pnl"]
                if db > 0 and dc > 0:
                    verdict = "**改善（両期間）**"
                elif db < 0 and dc < 0:
                    verdict = "悪化（両期間）"
                else:
                    verdict = "不安定"
            rows.append((lid, db, dc, verdict))

        order = {"**改善（両期間）**": 0, "悪化（両期間）": 1, "不安定": 2, "判定不能": 3}
        rows.sort(key=lambda r: (order[r[3]], -(r[1] or -9e9)))
        for lid, db, dc, verdict in rows:
            ds = f"{db:+.3f}" if db is not None else "—"
            cs = f"{dc:+.3f}" if dc is not None else "—"
            lines.append(f"| `{lid}` | {ds} | {cs} | {verdict} |")
        lines.append("")

        good = [r[0] for r in rows if r[3].startswith("**")]
        bad = [r[0] for r in rows if r[3].startswith("悪化")]
        lines.append(f"両期間で改善: {', '.join('`'+x+'`' for x in good) if good else 'なし'}")
        lines.append("")
        lines.append(f"両期間で悪化: {', '.join('`'+x+'`' for x in bad) if bad else 'なし'}")
        lines.append("")

    lines += ["## 両期間で符号がプラスだった変種（絶対値）", ""]
    both_pos = [
        (lid, b[lid], c[lid])
        for lid in b
        if lid in c
        and b[lid]["avg_trade_pnl"] > 0
        and c[lid]["avg_trade_pnl"] > 0
        and min(b[lid]["trades"], c[lid]["trades"]) >= MIN_N
    ]
    if both_pos:
        lines.append("| logic | nB | EV(B) | nC | EV(C) | ゲート |")
        lines.append("|-------|----|-------|----|-------|--------|")
        for lid, rb, rc in sorted(both_pos, key=lambda x: -x[2]["avg_trade_pnl"]):
            gate = ("B" if rb["gate_pass"] else "") + ("C" if rc["gate_pass"] else "")
            lines.append(
                f"| `{lid}` | {rb['trades']} | {rb['avg_trade_pnl']:+.3f} | "
                f"{rc['trades']} | {rc['avg_trade_pnl']:+.3f} | {gate or '—'} |"
            )
    else:
        lines.append("- なし")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
