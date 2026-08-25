"""Per-period and pooled significance for a batch of logics.

Needed because narrowing to one symbol removes the way trades were gathered.
A daily-scale logic on BTC-USDT alone fires roughly 22 times a year, so a
2.6-year period holds about 55 trades and ``min_trades=100`` cannot be reached
per period no matter how the history is cut. The question then is not "does it
pass" but "how much would n have to be", which is a property of the strategy's
own noise:

    SE = sd / sqrt(n),  t = EV / SE,  n@t=2 = (2 * sd / EV)^2

Reporting n@t=2 turns the gate from a number someone picked into a number the
data implies. If it lands near 100, the existing gate was calibrated; if it
lands at 1000, the logic was never going to be provable on this history.

Usage:
    python scripts/pooled_significance.py --reports eval/reports/20260824-slow-btc-long-set{A,B,C}.json \
        --out eval/reports/20260824-slow-btc-long-significance.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def tstat(pnl: np.ndarray) -> float:
    if len(pnl) < 2:
        return float("nan")
    sd = pnl.std(ddof=1)
    if sd == 0:
        return float("nan")
    return float(pnl.mean() / (sd / math.sqrt(len(pnl))))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="期間別・プール後の有意性")
    args = ap.parse_args()

    per_set: dict[str, dict[str, dict]] = {}
    order: list[str] = []
    for path in args.reports:
        for row in json.loads(Path(path).read_text(encoding="utf-8")):
            per_set.setdefault(row["logic_id"], {})[row["set"]] = row
            if row["set"] not in order:
                order.append(row["set"])

    lines = [
        f"# {args.title}",
        "",
        "1銘柄では期間ごとに `min_trades` に届かないので、合否ではなく",
        "**符号の一致（機構の再現性）** と **プール後の t 値（推定の精度）** で読む。",
        "`n@t=2` はその変種のばらつきから逆算した必要トレード数で、",
        "ゲートの 100 が妥当かどうかの根拠になる。",
        "",
        "| logic | " + " | ".join(f"Set {s} n / EV / t" for s in order) + " | プール n / EV / t | sd | n@t=2 |",
        "|---|" + "|".join(["---"] * (len(order) + 3)) + "|",
    ]

    summary = []
    for logic_id, sets in per_set.items():
        cells, pooled = [], []
        for s in order:
            row = sets.get(s)
            if row is None:
                cells.append("—")
                continue
            trades = pd.read_csv(Path(row["artifacts_dir"]) / "trades.csv")
            pnl = trades["pnl"].to_numpy()
            pooled.extend(pnl.tolist())
            cells.append(f"{len(pnl)} / {pnl.mean():+.3f} / {tstat(pnl):+.2f}")
        allp = np.array(pooled)
        t = tstat(allp)
        sd = allp.std(ddof=1)
        need = (2.0 * sd / allp.mean()) ** 2 if allp.mean() > 0 else float("inf")
        lines.append(
            f"| `{logic_id}` | " + " | ".join(cells) + f" | **{len(allp)} / {allp.mean():+.3f} "
            f"/ {t:+.2f}** | {sd:.2f} | {need:.0f} |"
        )
        summary.append((logic_id, len(allp), allp.mean(), t, need))

    n_periods = sum(1 for sets in per_set.values() for _ in sets)
    n_pos = sum(
        1
        for sets in per_set.values()
        for row in sets.values()
        if row["avg_trade_pnl"] > 0
    )
    sig = [s for s in summary if s[3] >= 2.0]
    lines += [
        "",
        f"- 期間×変種のうち EV プラス: **{n_pos} / {n_periods}**",
        f"- プール後に t ≥ 2: **{len(sig)} / {len(summary)}**",
        "",
    ]
    if sig:
        lines.append("プール後に t ≥ 2 だった変種:")
        lines.append("")
        for logic_id, n, ev, t, need in sorted(sig, key=lambda x: -x[3]):
            lines.append(f"- `{logic_id}` — n={n}, EV {ev:+.3f}, t {t:+.2f}（必要 n {need:.0f}）")
        lines.append("")

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
