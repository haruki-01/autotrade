"""固定ブラケット検証を3期間まとめて読む。

判定を理論値ではなく**対照（無作為エントリー）**に対して行う。
同じ足で損切りと利確の両方に触った場合を損切り優先にしているので、
計測系そのものが理論値より低く出る。対照を基準にすればそのバイアスが
両側で打ち消える。

Usage:
    python scripts/analyze_bracket.py --glob 'eval/reports/20260825-bracket15-set*.json' \\
        --stop 0.007 --rr 1.5 --maker-entry --out eval/reports/20260825-bracket15-summary.md
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.strategy.bracket import RR, STOP_PCT  # noqa: E402

MAKER = 0.0002


def _z_multi(n_trials: int) -> float:
    """Bonferroni 両側 5% に相当する z。scipy 無しで近似する。"""
    if n_trials <= 1:
        return 1.96
    # 正規の両側 p = 0.05/n の分位点。
    p = 0.025 / n_trials
    # Acklam の近似で十分（z≈2.5〜3.5 の範囲）
    t = math.sqrt(-2.0 * math.log(p))
    return t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / (
        1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--glob", default="eval/reports/20260825-bracket-set*.json")
    ap.add_argument("--out", default="eval/reports/20260825-bracket-summary.md")
    ap.add_argument("--stop", type=float, default=None)
    ap.add_argument("--rr", type=float, default=None)
    ap.add_argument("--maker-entry", action="store_true")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    stop = args.stop if args.stop is not None else STOP_PCT
    rr = args.rr if args.rr is not None else RR
    rows = []
    for path in sorted(glob.glob(args.glob)):
        rows.extend(json.loads(Path(path).read_text(encoding="utf-8")))
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("no bracket reports found")

    df["resolved"] = df["wins"] + df["losses"]
    agg = (
        df.groupby("logic_id")
        .agg(
            why=("why", "first"),
            sets=("set", "nunique"),
            n=("trades", "sum"),
            resolved=("resolved", "sum"),
            wins=("wins", "sum"),
            per_month=("per_month", "mean"),
            ev=("ev_usdt", "mean"),
            resolve_rate=("resolve_rate", "mean"),
        )
        .reset_index()
    )
    agg["win_rate"] = agg["wins"] / agg["resolved"]

    ctrl = agg[agg["logic_id"].str.startswith("br_random")]
    ctrl_wins = int(ctrl["wins"].sum())
    ctrl_res = int(ctrl["resolved"].sum())
    ctrl_rate = ctrl_wins / ctrl_res

    def z_vs_ctrl(w: int, r: int) -> float:
        if r == 0:
            return float("nan")
        p = (w + ctrl_wins) / (r + ctrl_res)
        se = np.sqrt(p * (1 - p) * (1 / r + 1 / ctrl_res))
        return (w / r - ctrl_rate) / se if se > 0 else float("nan")

    agg["z_ctrl"] = [z_vs_ctrl(int(w), int(r)) for w, r in zip(agg["wins"], agg["resolved"])]
    agg = agg.sort_values("z_ctrl", ascending=False)

    notional = cfg.margin_per_trade * cfg.leverage
    taker = cfg.fee_rate_per_side
    slip = cfg.slippage_pct_per_side
    w0 = 1.0 / (1.0 + rr)
    if args.maker_entry:
        cost = MAKER + w0 * MAKER + (1 - w0) * (taker + slip)
        fee_label = "入口メイカー / 利確メイカー / 損切り成行"
    else:
        cost = (taker + slip) * 2
        fee_label = "両側テイカー"
    be = (1 + cost / stop) / (1 + rr)

    L = [
        "# 固定ブラケット検証 — 3期間まとめ",
        "",
        f"BTCUSDT 15分足 ／ 損切り **{stop*100:.2f}%** ／ 利確 "
        f"**{stop*rr*100:.2f}%**（1:{rr:.1f}）／ 保有上限 **6時間** ／ 同時建玉 1",
        f"手数料前提: {fee_label}（往復 {cost*100:.4f}% = 許容損失の {cost/stop*100:.1f}%）",
        f"条件 {len(agg)} 本 × 3期間 = **{len(df)} 通り**、合計 {int(df['trades'].sum()):,} トレード",
        "",
        "## 判定の基準線",
        "",
        f"- 理論値 **{w0*100:.1f}%** — ドリフトのない価格での 1:{rr:.1f} 当たり率",
        f"- 実測の対照 **{ctrl_rate*100:.1f}%**（無作為エントリー n={ctrl_res:,}）",
        f"  同足で両方に触ったら損切り優先にしているので、計測系が理論より "
        f"{(w0-ctrl_rate)*100:.1f}pt 低く出る。**判定はこの対照を基準にする**",
        f"- 損益分岐 **{be*100:.1f}%**",
        "",
        f"対照から損益分岐までの距離は **+{(be-ctrl_rate)*100:.1f}pt**。ここを超える条件を探した。",
        "",
        "## 結果（対照との差の順）",
        "",
        "| logic | 狙い | 合計n | 回/月 | 決済率 | 勝率 | 対照比 | z | EV(USDT) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in agg.iterrows():
        tag = " *(対照)*" if r["logic_id"].startswith("br_random") else ""
        L.append(
            f"| `{r['logic_id']}`{tag} | {r['why']} | {int(r['n']):,} "
            f"| {r['per_month']:.1f} | {r['resolve_rate']*100:.1f}% "
            f"| **{r['win_rate']*100:.1f}%** | {(r['win_rate']-ctrl_rate)*100:+.1f}pt "
            f"| {r['z_ctrl']:+.2f} | {r['ev']:+.4f} |"
        )

    real = agg[~agg["logic_id"].str.startswith("br_random")]
    sig = real[real["z_ctrl"] >= 2]
    best = real.iloc[0]
    n_trials = len(real)
    z_cut = _z_multi(n_trials)
    n_multi = int((real["z_ctrl"] >= z_cut).sum())
    se_best = 100 * np.sqrt(ctrl_rate * (1 - ctrl_rate) / best["resolved"])
    need = be - ctrl_rate
    got = best["win_rate"] - ctrl_rate
    L += [
        "",
        "## まとめ",
        "",
        f"- 検証した条件: **{len(real)}**（対照2本を除く）／ 総トレード "
        f"**{int(df['trades'].sum()):,}**",
        f"- 対照を有意に上回った（z ≥ 2）: **{len(sig)}**",
        f"- 多重検定後（z ≥ {z_cut:.1f}）: **{n_multi}**",
        f"- 損益分岐（{be*100:.1f}%）を超えた: "
        f"**{int((real['win_rate'] >= be).sum())}**",
        f"- 費用後に黒字: **{int((real['ev'] > 0).sum())}**",
        f"- 月50回以上: **{int((real['per_month'] >= 50).sum())}**",
        "",
        f"最良は `{best['logic_id']}`（{best['why']}）で勝率 {best['win_rate']*100:.1f}%、"
        f"対照比 {(best['win_rate']-ctrl_rate)*100:+.1f}pt、z={best['z_ctrl']:+.2f}。",
        f"損益分岐まであと **{(be-best['win_rate'])*100:.1f}pt**。",
        "",
        "## EV とコスト",
        "",
        f"- EV の範囲: {real['ev'].min():+.4f} 〜 {real['ev'].max():+.4f} USDT",
        f"- 往復コスト: **−{notional*cost:.4f} USDT**",
        "",
        "## この枠で分かったこと",
        "",
        f"1. **頻度の要件（月50回）はこの枠なら簡単**。1枠でも月"
        f"{int(real['per_month'].max())}回まで撃てる",
        f"2. **最大の上振れは対照比 +{got*100:.1f}pt**。"
        f"必要な +{need*100:.1f}pt に対し {100*got/max(need, 1e-9):.0f}% まで来ている",
        f"3. 往復コストは許容損失の {cost/stop*100:.1f}%",
        "",
        "### この結論はどれくらい確かか",
        "",
        f"合計 {int(df['trades'].sum()):,} トレード。最大の条件（n={int(best['n']):,}）で"
        f"勝率の標準誤差は {se_best:.2f}pt。",
        f"z ≥ 2 が {len(sig)} 本 / {n_trials} 本。"
        f"多重検定の閾値 z ≥ {z_cut:.1f} を超えたのは {n_multi} 本。",
        "",
    ]

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
