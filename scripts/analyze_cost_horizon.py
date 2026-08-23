"""How long must a trade be held before costs stop dominating?

217 evaluations produced edges of the same size as the round-trip cost. That is
a structural problem, not a signal-quality problem, so measure it directly and
without reference to any strategy: how big is the typical move on each
timeframe, and what fraction of the risk budget does the cost eat there?

Usage:
    python scripts/analyze_cost_horizon.py --out eval/reports/<name>.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import LOCK_PATH, load_eval_config, load_locked_frames  # noqa: E402

import yaml  # noqa: E402

# Stop distances are quoted in ATR multiples throughout this project.
STOP_ATR_MULTS = [1.5, 2.0, 3.0]
# A cost worth this fraction of the risk budget is the most we want to pay.
COST_BUDGET_OF_R = 0.05


def resample(m15: pd.DataFrame, rule: str) -> pd.DataFrame:
    return (
        m15.resample(rule, label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(period, min_periods=period).mean()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v1.yaml")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    lock = yaml.safe_load(LOCK_PATH.read_text(encoding="utf-8"))

    fee = cfg.fee_rate_per_side
    slip = cfg.slippage_pct_per_side
    cost_pct = (fee + slip) * 2 * 100.0
    notional = cfg.margin_per_trade * cfg.leverage
    cost_usdt = notional * cost_pct / 100.0

    lines = [
        "# コストが無視できる時間軸はどこか",
        "",
        "戦略と無関係に、値幅とコストの比だけを測る。"
        "217本の評価でエッジがコストと同じ大きさだったので、"
        "「どの時間軸なら勝負になるか」を先に確定させる。",
        "",
        "## 前提となるコスト",
        "",
        "| 項目 | 値 |",
        "|------|-----|",
        f"| 手数料（片道） | {fee * 100:.3f}% |",
        f"| スリッページ（片道） | {slip * 100:.3f}% |",
        f"| **往復コスト** | **{cost_pct:.3f}%（元本比）** |",
        f"| 想定元本 | {notional:.0f} USDT |",
        f"| 1トレードのコスト | {cost_usdt:.4f} USDT |",
        "",
        "## 時間軸ごとの値幅（ATR14 の中央値、終値比）",
        "",
        "`cost/R` は「損切りまでの距離を 1R としたとき、コストが R の何%か」。"
        f"ここが {COST_BUDGET_OF_R * 100:.0f}% を超えると、勝率や期待値の議論より先にコストで負ける。",
        "",
    ]

    header = "| 期間 | 足 | ATR中央値 | " + " | ".join(
        f"cost/R (stop {m}ATR)" for m in STOP_ATR_MULTS
    ) + " |"
    sep = "|------|-----|-----------|" + "|".join(["----------"] * len(STOP_ATR_MULTS)) + "|"
    lines += [header, sep]

    verdicts: dict[str, list[float]] = {}
    for set_name in ("A", "B", "C"):
        frames, _ = load_locked_frames(lock, set_name)
        m15 = frames["15m"]
        start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
        end = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
        for label, rule in (("15m", "15min"), ("1h", "1h"), ("4h", "4h"), ("1d", "1D")):
            bars = resample(m15, rule) if rule != "15min" else m15
            a = atr(bars) / bars["close"] * 100.0
            a = a[(a.index >= start) & (a.index < end)].dropna()
            if a.empty:
                continue
            med = float(a.median())
            ratios = [cost_pct / (med * m) * 100.0 for m in STOP_ATR_MULTS]
            verdicts.setdefault(label, []).extend(ratios)
            cells = " | ".join(f"{r:.1f}%" for r in ratios)
            lines.append(f"| Set {set_name} | {label} | {med:.3f}% | {cells} |")

    lines += ["", "## 読み取り", ""]
    for label in ("15m", "1h", "4h", "1d"):
        rs = verdicts.get(label)
        if not rs:
            continue
        worst, best = max(rs), min(rs)
        ok = best <= COST_BUDGET_OF_R * 100.0
        mark = "**使える**" if ok else "コスト負け"
        lines.append(
            f"- **{label}**: cost/R は {best:.1f}〜{worst:.1f}% → {mark}"
        )

    lines += [
        "",
        "損切りを ATR の何倍に置くかで割り引けるが、"
        "**足を遅くするほうが効き方が大きい**（ATR そのものが数倍になる）。",
        "",
        "## 必要な ATR 水準（逆算）",
        "",
        f"cost/R を {COST_BUDGET_OF_R * 100:.0f}% 以下に抑えるには、"
        "`ATR% >= 往復コスト% / (0.05 × 損切りATR倍率)` が必要。",
        "",
        "| 損切り | 必要な ATR（終値比） |",
        "|--------|----------------------|",
    ]
    for m in STOP_ATR_MULTS:
        need = cost_pct / (COST_BUDGET_OF_R * m)
        lines.append(f"| {m} ATR | {need:.2f}% 以上 |")

    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
