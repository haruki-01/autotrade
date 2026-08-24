"""Is the slow pack an edge, or just leveraged exposure to a rising market?

2023, 2024 and 2025-26 were all broadly up for crypto, so a long-biased trend
system will look good in every period tested. This compares each strategy
against simply holding the basket, and reports how much of the time the
strategy was actually exposed.

Usage:
    python scripts/benchmark_buy_and_hold.py --report eval/reports/<tag>-set<X>.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.eval.multi import MULTI_LOCK_PATH, load_multi_frames  # noqa: E402


def buy_and_hold(lock: dict, cfg, set_name: str) -> tuple[dict[str, float], float]:
    start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
    end = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
    per: dict[str, float] = {}
    curves: list[pd.Series] = []
    for symbol in lock["datasets"][set_name]["symbols"]:
        m15 = load_multi_frames(lock, set_name, symbol)["15m"]
        w = m15[(m15.index >= start) & (m15.index < end)]
        norm = w["close"] / w["close"].iloc[0]
        per[symbol] = float(norm.iloc[-1] - 1.0) * 100.0
        curves.append(norm)
    basket = pd.concat(curves, axis=1).ffill().mean(axis=1)
    dd = float((basket / basket.cummax() - 1.0).min()) * -100.0
    return per, {"return_pct": float(basket.iloc[-1] - 1.0) * 100.0, "max_dd_pct": dd}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v2.yaml")
    ap.add_argument("--lock", default=str(MULTI_LOCK_PATH))
    ap.add_argument("--reports", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    lock = yaml.safe_load(Path(args.lock).read_text(encoding="utf-8"))

    lines = [
        "# SH-01 は本当にエッジか、それとも上昇相場に乗っていただけか",
        "",
        "2023 / 2024 / 2025-26 はいずれも暗号資産が上昇した期間なので、"
        "ロング寄りのトレンド追随はどの期間でも good に見える。"
        "**買い持ちと比べて意味があるか**を確認する。",
        "",
    ]

    for report_path in args.reports:
        rows = json.loads(Path(report_path).read_text(encoding="utf-8"))
        set_name = rows[0]["set"]
        per, bh = buy_and_hold(lock, cfg, set_name)
        ew = bh["return_pct"]

        lines += [
            f"## Set {set_name}（{cfg.sets[set_name].start} 〜 {cfg.sets[set_name].end}）",
            "",
            f"買い持ち（無レバ・等加重）: リターン **{ew:+.1f}%** / 最大DD **{bh['max_dd_pct']:.1f}%**",
            "",
            "銘柄別リターン:",
            "",
            "| " + " | ".join(per) + " | 等加重平均 |",
            "|" + "|".join(["---"] * (len(per) + 1)) + "|",
            "| " + " | ".join(f"{v:+.1f}%" for v in per.values()) + f" | **{ew:+.1f}%** |",
            "",
            "生リターンの比較は投下資本が違う分だけ戦略に不利になる"
            f"（`fixed_margin` は1銘柄あたり証拠金 {cfg.margin_per_trade:.0f} / 元本 "
            f"{cfg.initial_equity:.0f} しか使わない）。"
            "`fixed_margin` ではリスク額を k 倍するとリターンもDDもほぼ k 倍になるので、"
            "**リターン ÷ DD** が資本量に依らない比較になる。",
            "",
            "| logic | 戦略リターン | 買い持ち | 差 | 戦略DD | 買い持ちDD "
            "| 戦略 ret/DD | 買い持ち ret/DD | n |",
            "|-------|-------------|----------|-----|--------|-----------|---|---|---|",
        ]
        bh_ratio = ew / bh["max_dd_pct"] if bh["max_dd_pct"] else float("nan")
        for r in sorted(rows, key=lambda x: -x["total_return_pct"]):
            diff = r["total_return_pct"] - ew
            ratio = (
                r["total_return_pct"] / r["max_drawdown_pct"]
                if r["max_drawdown_pct"]
                else float("nan")
            )
            lines.append(
                f"| `{r['logic_id']}` | {r['total_return_pct']:+.1f}% | {ew:+.1f}% "
                f"| {diff:+.1f}pt | {r['max_drawdown_pct']:.1f}% | {bh['max_dd_pct']:.1f}% "
                f"| **{ratio:+.2f}** | {bh_ratio:+.2f} | {r['trades']} |"
            )
        beat = sum(1 for r in rows if r["total_return_pct"] > ew)
        beat_ratio = sum(
            1
            for r in rows
            if r["max_drawdown_pct"] and r["total_return_pct"] / r["max_drawdown_pct"] > bh_ratio
        )
        lines += [
            "",
            f"生リターンで買い持ちを上回った変種: **{beat} / {len(rows)}**",
            "",
            f"リターン÷DD で買い持ちを上回った変種: **{beat_ratio} / {len(rows)}**",
            "",
        ]

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
