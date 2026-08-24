"""How often did everything we have already tested actually trade?

The frequency requirement (entries per month) was added after most of the
inventory had been evaluated, so nothing recorded so far was selected for it.
Before designing anything new, read the existing runs against it: the answer
decides whether the requirement needs a new family of logic or just a looser
filter on an existing one.

Also prices the requirement. Every entry pays a fixed round trip, so a rate
target is a cost target:

    cost/trade  = margin * leverage * (fee + slippage) * 2
    cost/year   = cost/trade * rate * 12
    net EV needed for R% a year = (equity * R/100 + cost/year) / (rate * 12) - cost/trade

Usage:
    python scripts/trade_rate_audit.py --config configs/eval_v3_btc.yaml
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402

# Set windows differ between eval versions, so months are keyed by the report
# name rather than by the set letter alone.
SET_MONTHS: dict[str, dict[str, float]] = {
    "v1v2": {"A": 12.0, "B": 12.0, "C": 19.8},
    "v3": {"A": 31.0, "B": 32.0, "C": 31.7},
}


def months_for(report_name: str, set_name: str) -> float:
    table = SET_MONTHS["v3"] if "btc-long" in report_name or "btc-rate" in report_name else SET_MONTHS["v1v2"]
    return table.get(set_name, 12.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--reports-glob", default="eval/reports/*set*.json")
    ap.add_argument("--out", default="eval/reports/20260824-trade-rate-audit.md")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    target = cfg.min_trades_per_month
    notional = cfg.margin_per_trade * cfg.leverage
    cost = notional * (cfg.fee_rate_per_side + cfg.slippage_pct_per_side) * 2

    records = []
    for path in sorted(glob.glob(args.reports_glob)):
        name = Path(path).stem
        try:
            rows = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(rows, list) or not rows or "logic_id" not in rows[0]:
            continue
        for r in rows:
            if "trades" not in r or "set" not in r:
                continue
            m = months_for(name, r["set"])
            records.append(
                {
                    "report": name,
                    "family": r.get("family") or r.get("hypothesis_id") or "—",
                    "logic_id": r["logic_id"],
                    "set": r["set"],
                    "trades": r["trades"],
                    "per_month": r["trades"] / m if m else 0.0,
                    "ev": r.get("avg_trade_pnl", 0.0),
                }
            )

    df = pd.DataFrame(records)
    if df.empty:
        raise SystemExit("no reports matched")

    best = df.sort_values("per_month", ascending=False).drop_duplicates("logic_id")

    lines = [
        "# これまでのロジックは月に何回撃っていたか",
        "",
        f"要件: **月 {target:.0f} エントリー以上**（入口判断は {cfg.max_entry_timeframe} 以下）。",
        "この要件は既存の検証が全部終わったあとに追加したので、",
        "**記録済みのロジックは一つもこの条件で選ばれていない**。まず現状を測る。",
        "",
        "## コストの見積り",
        "",
        f"- 1トレードの想定元本: 証拠金 {cfg.margin_per_trade:.0f} × レバ {cfg.leverage:.0f} "
        f"= **{notional:.0f} USDT**",
        f"- 往復コスト: {notional:.0f} × ({cfg.fee_rate_per_side*100:.3f}% + "
        f"{cfg.slippage_pct_per_side*100:.2f}%) × 2 = **{cost:.3f} USDT/回**",
        "",
        "| 月あたり | 年間回数 | 年間コスト | 元本比 | 年10%に必要な純EV | 年20% | 年30% |",
        "|---|---|---|---|---|---|---|",
    ]
    for rate in (10, 25, 50, 100, 200):
        per_year = rate * 12
        cost_year = per_year * cost
        cells = []
        for target_pct in (10, 20, 30):
            need = (cfg.initial_equity * target_pct / 100.0) / per_year
            cells.append(f"{need:+.3f}")
        flag = " ←要件" if rate == target else ""
        lines.append(
            f"| {rate}{flag} | {per_year} | {cost_year:.0f} USDT "
            f"| {100*cost_year/cfg.initial_equity:.0f}% | " + " | ".join(cells) + " |"
        )

    lines += [
        "",
        f"純EV は費用控除後。年600回なら年間 {600*cost:.0f} USDT ＝ "
        f"元本 {cfg.initial_equity:.0f} の {100*600*cost/cfg.initial_equity:.0f}% を"
        "コストとして払った上での数字。",
        "",
        "## 記録済みロジックの実績（変種ごとの最高頻度）",
        "",
        f"| 系統 | logic | set | n | 月あたり | EV | 要件({target:.0f}/月)まで |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in best.head(25).iterrows():
        gap = target / r["per_month"] if r["per_month"] > 0 else float("inf")
        lines.append(
            f"| {r['family']} | `{r['logic_id']}` | {r['set']} | {r['trades']} "
            f"| **{r['per_month']:.1f}** | {r['ev']:+.3f} | {gap:.0f}倍 |"
        )

    meets = best[best["per_month"] >= target]
    lines += [
        "",
        f"- 記録済み {len(best)} ロジックのうち、月 {target:.0f} 回に到達: "
        f"**{len(meets)}**",
        f"- 最高頻度: {best['per_month'].max():.1f} 回/月（要件の "
        f"{100*best['per_month'].max()/target:.0f}%）",
        f"- 中央値: {best['per_month'].median():.1f} 回/月",
        "",
        "## 頻度とEVの関係（フロンティア）",
        "",
        "全記録（変種×期間）を頻度帯に分け、その帯で**実際に到達できた最良のEV**と、",
        "その頻度で年20%を出すのに**必要なEV**を並べる。",
        "必要線を上回っている帯があれば、そこが狙う場所。",
        "",
        "| 頻度帯（回/月） | 記録数 | 最良EV | EVプラスの割合 | 年20%に必要 | 到達 |",
        "|---|---|---|---|---|---|",
    ]

    bands = [(0, 5), (5, 10), (10, 25), (25, 50), (50, 100), (100, 10**9)]
    for lo, hi in bands:
        band = df[(df["per_month"] >= lo) & (df["per_month"] < hi)]
        if band.empty:
            continue
        mid = (lo + min(hi, 200)) / 2
        need = (cfg.initial_equity * 0.20) / (mid * 12)
        best_ev = band["ev"].max()
        share = 100.0 * (band["ev"] > 0).mean()
        label = f"{lo}〜{hi}" if hi < 10**9 else f"{lo}+"
        lines.append(
            f"| {label} | {len(band)} | **{best_ev:+.3f}** | {share:.0f}% "
            f"| {need:+.3f} | {'○' if best_ev >= need else '×'} |"
        )

    hi_freq = df[df["per_month"] >= target]
    lines += [
        "",
        f"月 {target:.0f} 回以上の記録は **{len(hi_freq)} 件**あり、"
        f"EV の最良は **{hi_freq['ev'].max():+.3f}**、"
        f"プラスは **{int((hi_freq['ev'] > 0).sum())} 件**。",
        "",
        "ただしこの帯の記録はほぼ EH 系（15分足・1時間ATR損切り）の緩い変種と対照で、",
        "**頻度を狙って設計したものではない**。「+0.004 が上限」ではなく",
        "「頻度を狙わずに作ったものは、この帯では全部負けた」と読むべき。",
        "",
        "## コスト前提の感度",
        "",
        "月50回では手数料の置き方が結果を支配する。現行は**両側テイカー + 両側スリッページ**。",
        "指値で入れれば入口はメイカーになる。",
        "",
        "| 前提 | 往復コスト率 | 往復コスト | 年600回のコスト | 元本比 |",
        "|---|---|---|---|---|",
    ]
    maker = 0.0002
    scenarios = [
        ("現行（両側テイカー）", cfg.fee_rate_per_side * 2 + cfg.slippage_pct_per_side * 2),
        ("入口メイカー / 出口テイカー", maker + cfg.fee_rate_per_side + cfg.slippage_pct_per_side),
        ("両側メイカー", maker * 2 + cfg.slippage_pct_per_side),
    ]
    for label, rate in scenarios:
        c = notional * rate
        lines.append(
            f"| {label} | {rate*100:.3f}% | **{c:.3f} USDT** "
            f"| {c*600:.0f} USDT | {100*c*600/cfg.initial_equity:.0f}% |"
        )
    lines += [
        "",
        "入口を指値にするだけで年間コストが "
        f"{scenarios[0][1]*notional*600:.0f} → {scenarios[1][1]*notional*600:.0f} USDT。"
        "月2回のロジックでは無視できた差が、月50回では最大の設計変数になる。"
        "ただし指値は約定しないことがあるので、**未約定を数えるバックテスト**が先に必要。",
        "",
    ]

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
