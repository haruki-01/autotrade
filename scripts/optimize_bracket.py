"""リスクリワード比と幅の組み合わせを総当たりし、必要上振れが最小の形を探す。

変数は3つで、順番に決まる:

  1. リスクリワード比 RR
  2. 比が決まったあとの損切り幅 s
  3. 上記から決まる必要勝率

必要勝率は理論から出る。ドリフトのない価格での当たり率（帰無仮説）と、
費用を引いて黒字になる勝率（損益分岐）は

    帰無     w0 = 1 / (1 + RR)
    損益分岐 w* = (1 + c/s) / (1 + RR)          c = 往復コスト率

なので、**必要上振れ**は差を取って

    w* - w0 = (c/s) / (1 + RR)                 ... (絶対値, ポイント)
    w* / w0 = 1 + c/s                          ... (相対値, 倍率)

ここが要点。**相対値は RR に依存せず、幅だけで決まる。** 一方、絶対値は
RR を上げると小さくなる。どちらで読むべきかは「シグナルが確率をどう動かすか」
で決まるので、幾何ブラウン運動での上振れ量から逆算する。

ドリフト μ・分散 σ² の価格に対し、下 s・上 RR·s の二重障壁の当たり率は
小さい μ で展開すると

    P ≈ 1/(1+RR) + θ · s · RR / (2(1+RR))      θ = 2μ/σ²

これが必要上振れ (c/s)/(1+RR) を超える条件は

    **θ ≥ 2c / (s² · RR)**

つまり**必要なシグナル強度は幅の2乗と RR に反比例する**。幅を広げるほうが
効きが大きい（2乗）。これが探索の指針になる。

制約は保有上限6時間・同時建玉1枠なので、幅を広げるとタイムアウトが増えて
トレード回数が落ちる。回数の下限（月50回）を満たす範囲で θ を最小化する。

Usage:
    python scripts/optimize_bracket.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.eval.multi import load_multi_frames  # noqa: E402
from autotrade.strategy.bracket import scan_bracket  # noqa: E402

BARS_PER_HOUR = 4
MAKER = 0.0002


def blended_cost(
    *, maker: float, taker: float, slip: float, win_share: float, maker_entry: bool
) -> float:
    """入口指値・利確指値・損切り成行を前提にした往復コスト率。

    損切りは成行にせざるを得ない（指値だと急落で約定しない）。1:2 なら
    出口の2/3が損切り側なので、出口はテイカー寄りになる。
    スリッページもテイカー側の脚にだけ乗せる。
    """
    entry_fee = maker if maker_entry else taker
    entry_slip = 0.0 if maker_entry else slip
    # 出口: 利確は指値で置けるのでメイカー、損切り/タイムアウトは成行
    exit_fee = win_share * maker + (1 - win_share) * taker
    exit_slip = (1 - win_share) * slip
    return entry_fee + entry_slip + exit_fee + exit_slip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v3_btc.lock.yaml")
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--max-hours", type=float, default=6.0)
    ap.add_argument("--min-per-month", type=float, default=50.0)
    # 決済率が低いと「1:RR のブラケット」ではなく「6時間で成行決済」になり、
    # θ の導出（障壁に到達する前提の展開）が成り立たなくなる。下限で守る。
    ap.add_argument("--min-resolve", type=float, default=0.70)
    ap.add_argument("--sample", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="eval/reports/20260825-bracket-optimize.md")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    with open(args.lock, encoding="utf-8") as f:
        lock = yaml.safe_load(f)
    max_bars = int(round(args.max_hours * BARS_PER_HOUR))
    taker = cfg.fee_rate_per_side
    slip = cfg.slippage_pct_per_side

    rr_grid = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    stop_grid = [0.0025, 0.0035, 0.005, 0.007, 0.010, 0.014, 0.020]

    # 各期間の価格を読み、無作為エントリーで当たり率と保有時間を実測する
    series = []
    for set_name in [s.strip() for s in args.sets.split(",")]:
        frames = load_multi_frames(lock, set_name, "BTCUSDT")
        df = frames["15m"]
        lo = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
        hi = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
        df = df.loc[(df.index >= lo) & (df.index <= hi)]
        series.append((set_name, df))

    rows = []
    for rr in rr_grid:
        for stop in stop_grid:
            res_rates, win_rates, holds = [], [], []
            for set_name, df in series:
                high = df["high"].to_numpy(float)
                low = df["low"].to_numpy(float)
                close = df["close"].to_numpy(float)
                rng = np.random.default_rng(args.seed)
                usable = len(close) - max_bars - 1
                entries = np.sort(
                    rng.choice(usable, size=min(args.sample, usable), replace=False)
                )
                for d in (1, -1):
                    r = scan_bracket(
                        high, low, close, entries,
                        direction=d, stop_pct=stop, rr=rr, max_bars=max_bars,
                    )
                    res_rates.append(r["resolve_rate"])
                    win_rates.append(r["win_rate_resolved"])
                    holds.append(r["mean_bars"])

            resolve = float(np.mean(res_rates))
            w_measured = float(np.mean(win_rates))
            mean_bars = float(np.mean(holds))
            w0 = 1.0 / (1.0 + rr)

            cost = blended_cost(
                maker=MAKER, taker=taker, slip=slip, win_share=w0, maker_entry=True
            )
            cost_taker = (taker + slip) * 2
            cost_r = cost / stop
            w_be = (1.0 + cost_r) / (1.0 + rr)
            uplift_pt = w_be - w0
            uplift_rel = cost_r  # w*/w0 - 1
            # 必要シグナル強度（θ ∝ 2c/(s²·RR)）。相対比較用に正規化する
            theta = 2.0 * cost / (stop**2 * rr)
            # 1枠・平均保有から出るトレード上限
            per_month = 720.0 / (mean_bars / BARS_PER_HOUR) if mean_bars > 0 else 0.0

            rows.append(
                {
                    "rr": rr,
                    "stop": stop,
                    "tp": stop * rr,
                    "resolve": resolve,
                    "w_measured": w_measured,
                    "w0": w0,
                    "w_be": w_be,
                    "uplift_pt": uplift_pt,
                    "uplift_rel": uplift_rel,
                    "theta": theta,
                    "cost_rate": cost,
                    "cost_taker": cost_taker,
                    "cost_r": cost_r,
                    "mean_bars": mean_bars,
                    "per_month_max": per_month,
                }
            )

    df_r = pd.DataFrame(rows)
    ok = df_r[
        (df_r["per_month_max"] >= args.min_per_month)
        & (df_r["resolve"] >= args.min_resolve)
    ].copy()
    best = ok.loc[ok["theta"].idxmin()] if not ok.empty else df_r.loc[df_r["theta"].idxmin()]
    base = df_r[(df_r["rr"] == 2.0) & (np.isclose(df_r["stop"], 0.0035))].iloc[0]

    L = [
        "# リスクリワード比と幅の総当たり — 必要上振れが最小の形を探す",
        "",
        f"BTCUSDT 15分足 ／ 保有上限 **{args.max_hours:.0f}時間** ／ 同時建玉 1 ／ "
        f"回数の下限 **月{args.min_per_month:.0f}回**",
        f"各セル {args.sample:,}点 × 3期間 × 両方向の無作為エントリーで実測。",
        "",
        "## 必要上振れは何で決まるか",
        "",
        "```",
        "帰無     w0 = 1 / (1 + RR)",
        "損益分岐 w* = (1 + c/s) / (1 + RR)      c = 往復コスト率, s = 損切り幅",
        "",
        "必要上振れ(pt)  = w* - w0 = (c/s) / (1 + RR)",
        "必要上振れ(倍率) = w* / w0 = 1 + c/s",
        "```",
        "",
        "**相対値は RR に依存せず、幅だけで決まります。** 絶対値(pt)は RR を上げると",
        "下がりますが、それは帰無の水準自体が下がるからで、難易度が下がったとは",
        "限りません。どちらで読むかを決めるため、シグナルが確率をどれだけ動かせるかを",
        "二重障壁の当たり率から展開しました。",
        "",
        "```",
        "ドリフト μ を与えたときの当たり率 ≈ 1/(1+RR) + θ·s·RR / (2(1+RR))",
        "                                              θ = 2μ/σ²",
        "",
        "必要上振れを超える条件:  θ ≥ 2c / (s² · RR)",
        "```",
        "",
        "**必要なシグナル強度は幅の2乗と RR に反比例します。**",
        "幅を広げるほうが効きが大きい（2乗で効く）。これが最後の列 θ です。",
        "小さいほど弱いシグナルでも黒字にできます。",
        "",
        "## 手数料の前提",
        "",
        "入口は指値（メイカー）、利確も指値で置ける（メイカー）、",
        "**損切りだけは成行にせざるを得ません**（指値だと急落で約定しない）。",
        "スリッページもテイカー側の脚にだけ乗せます。",
        "",
        f"- メイカー {MAKER*100:.3f}% ／ テイカー {taker*100:.3f}% ／ "
        f"スリッページ {slip*100:.3f}%",
        f"- 1:2 なら出口の約2/3が損切り側なので、往復 "
        f"**{base['cost_rate']*100:.4f}%**（両側テイカーなら {base['cost_taker']*100:.3f}%）",
        f"- **コストは約 {(1-base['cost_rate']/base['cost_taker'])*100:.0f}% 減ります**",
        "",
        "## 総当たり結果",
        "",
        "| RR | 損切り | 利確 | 6h決済率 | 平均保有 | 月上限 | 帰無 | 損益分岐 | 必要上振れ | 倍率 | θ（相対） |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    theta_min = float(ok["theta"].min()) if not ok.empty else float(df_r["theta"].min())
    for _, r in df_r.sort_values(["rr", "stop"]).iterrows():
        mark = ""
        if abs(r["theta"] - best["theta"]) < 1e-12:
            mark = " ←最良"
        elif r["resolve"] < args.min_resolve:
            mark = f" ✗決済率{args.min_resolve*100:.0f}%未満"
        elif r["per_month_max"] < args.min_per_month:
            mark = " ✗回数不足"
        L.append(
            f"| 1:{r['rr']:.1f} | {r['stop']*100:.2f}% | {r['tp']*100:.2f}% "
            f"| {r['resolve']*100:.0f}% | {r['mean_bars']/BARS_PER_HOUR:.1f}h "
            f"| {r['per_month_max']:.0f} | {r['w0']*100:.1f}% | {r['w_be']*100:.1f}% "
            f"| **{r['uplift_pt']*100:+.1f}pt** | ×{1+r['uplift_rel']:.2f} "
            f"| {r['theta']/theta_min:.2f}{mark} |"
        )

    L += [
        "",
        "θ は最小値を1として正規化しています（小さいほど弱いシグナルで足りる）。",
        "",
        f"## 最良: RR **1:{best['rr']:.1f}** ／ 損切り **{best['stop']*100:.2f}%** ／ "
        f"利確 **{best['tp']*100:.2f}%**",
        "",
        f"| | 現行（1:2, 0.35%, 両側テイカー） | 最良（指値） |",
        "|---|---|---|",
        f"| 6時間以内決済率 | {base['resolve']*100:.0f}% | {best['resolve']*100:.0f}% |",
        f"| 平均保有 | {base['mean_bars']/BARS_PER_HOUR:.1f}h | "
        f"{best['mean_bars']/BARS_PER_HOUR:.1f}h |",
        f"| 月の上限回数（1枠） | {base['per_month_max']:.0f} | {best['per_month_max']:.0f} |",
        f"| 往復コスト率 | {base['cost_taker']*100:.3f}% | {best['cost_rate']*100:.4f}% |",
        f"| コスト / 許容損失 | {base['cost_taker']/base['stop']*100:.1f}% | "
        f"{best['cost_r']*100:.1f}% |",
        f"| 帰無勝率 | {base['w0']*100:.1f}% | {best['w0']*100:.1f}% |",
        f"| 損益分岐勝率 | "
        f"{(1+base['cost_taker']/base['stop'])/(1+base['rr'])*100:.1f}% | "
        f"{best['w_be']*100:.1f}% |",
        f"| **必要上振れ** | "
        f"**+{((1+base['cost_taker']/base['stop'])/(1+base['rr'])-base['w0'])*100:.1f}pt** | "
        f"**+{best['uplift_pt']*100:.1f}pt** |",
        f"| 必要上振れ（倍率） | "
        f"×{1+base['cost_taker']/base['stop']:.2f} | ×{1+best['uplift_rel']:.2f} |",
        "",
    ]

    base_theta = 2.0 * base["cost_taker"] / (base["stop"] ** 2 * base["rr"])
    L += [
        f"必要シグナル強度 θ は **{base_theta/best['theta']:.1f}分の1** になります。",
        "内訳は指値化によるコスト減と、幅を広げたことの2乗の効き。",
        "",
        "## 幅を広げるとタイムアウトが増える — その損得",
        "",
        "タイムアウトは6時間で成行決済なので、損益はほぼゼロですがコストは満額払います。",
        "決済率が下がると「コストだけ払う取引」が増えます。",
        "ただし**必要上振れは幅の2乗で下がる**ので、割に合う範囲があります。",
        "",
        "| 損切り(RR=1:3) | 6h決済率 | タイムアウト | 月上限 | 必要上振れ | θ（相対） |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in df_r[df_r["rr"] == 3.0].sort_values("stop").iterrows():
        L.append(
            f"| {r['stop']*100:.2f}% | {r['resolve']*100:.0f}% "
            f"| {(1-r['resolve'])*100:.0f}% | {r['per_month_max']:.0f} "
            f"| +{r['uplift_pt']*100:.1f}pt | {r['theta']/theta_min:.2f} |"
        )

    L += [
        "",
        "## 決済率をどこまで譲るか — これが唯一の判断",
        "",
        "決済率90%は仮置きとのことなので、下限ごとに最良の形を出します。",
        "決済率を下げるほど幅を広げられ、必要上振れは下がりますが、",
        "**タイムアウト（損益ほぼゼロでコストだけ払う取引）が増えます**。",
        "",
        "| 決済率の下限 | 最良の RR | 損切り | 利確 | 実際の決済率 | 月上限 | 必要上振れ | 倍率 | θ（相対） |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for floor in (0.90, 0.85, 0.80, 0.75, 0.70, 0.60, 0.50):
        cand = df_r[
            (df_r["resolve"] >= floor) & (df_r["per_month_max"] >= args.min_per_month)
        ]
        if cand.empty:
            L.append(f"| {floor*100:.0f}% | — | — | — | — | — | — | — | — |")
            continue
        b = cand.loc[cand["theta"].idxmin()]
        L.append(
            f"| {floor*100:.0f}% | 1:{b['rr']:.1f} | {b['stop']*100:.2f}% "
            f"| {b['tp']*100:.2f}% | {b['resolve']*100:.0f}% | {b['per_month_max']:.0f} "
            f"| **+{b['uplift_pt']*100:.1f}pt** | ×{1+b['uplift_rel']:.2f} "
            f"| {b['theta']/theta_min:.1f} |"
        )

    L += [
        "",
        "決済率を 90% → 70% に譲るだけで必要上振れが大きく下がります。",
        "**ここが今いちばん効く判断です。**",
        "",
        "## なぜ決済率の下限が必要か",
        "",
        "下限を外すと最良は「RR 1:5・損切り2.00%」になりますが、これは決済率15%で、",
        "**85%が6時間のタイムアウト**。もはや 1:5 のブラケットではなく",
        "「6時間持って成行で決済」です。θ の導出は障壁に到達する前提の展開なので、",
        "この領域では式そのものが成り立ちません。",
        "",
        f"6時間の値動きの標準偏差は 15分足ATR({0.275:.3f}%) × √24 ≈ **1.35%** です。",
        "損切りと利確の合計幅がこれを超えると、ブラケットは届かなくなります。",
        "",
        "```",
        "損切り × (1 + RR) ≲ 1.35%     ブラケットが機能する条件",
        "```",
        "",
        "1:2 なら損切り 0.45% まで、1:3 なら 0.34% まで、1:5 なら 0.22% まで。",
        "**RR を上げると幅を狭めねばならず、コスト比が悪化します。**",
        "これが RR を無限に上げられない理由です。",
        "",
        "## funding は無視できる",
        "",
        "レバでポジションを持ち続けると funding が乗りますが、この枠では小さいです。",
        f"平均保有 {best['mean_bars']/BARS_PER_HOUR:.1f} 時間、funding は8時間ごとなので",
        f"1トレードあたりの発生回数は約 {best['mean_bars']/BARS_PER_HOUR/8:.2f} 回。",
        "BTC の funding は8時間で 0.01% 前後なので、",
        f"1トレードあたり約 {best['mean_bars']/BARS_PER_HOUR/8*0.0001*100:.4f}%。",
        f"往復コスト {best['cost_rate']*100:.4f}% の "
        f"{best['mean_bars']/BARS_PER_HOUR/8*0.0001/best['cost_rate']*100:.1f}% で、"
        "**判断を変える大きさではありません**。",
        "",
    ]

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
