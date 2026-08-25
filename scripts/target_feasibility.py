"""月次ROI目標と分散の上限から、必要なEVと取引回数を逆算する。

目標を決めると、1回あたりのEVと必要回数は自由に選べなくなる。使う関係は3つ。

  月次ROI  = e * N / E                      e=1回のEV(USDT), N=月の回数
  最大DD   ~ s^2 / (2e)                     s=1回の標準偏差。ドリフト付き
                                            ランダムウォークの期待最大DD
  枠数     = N * H / 720                    H=平均保有時間(h)

1番目と2番目を割ると、サイズが消える:

  ROI / DD = 2 * N * Q^2        Q = e/s（1回あたりのシャープ）

**これが本題。** ポジションを大きくすると ROI も DD も同じ倍率で増えるので、
「目標ROIをDD以内で達成できるか」はサイズと無関係に決まる。決めるのは Q と N だけ。

  必要条件:  N * Q^2 >= ROI / (2 * DD上限)

サイズは、この条件を満たしたあとに絶対水準を合わせるためのつまみにすぎない。
そしてサイズを上げると必要レバレッジが上がり、枠数を掛けた分だけ効く:

  必要レバ = 枠数 * (R / s_stop) / E        R=1回の許容損失, s_stop=損切り幅(%)

Usage:
    python scripts/target_feasibility.py --roi 120 --dd 20
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402

SET_MONTHS_V1V2 = {"A": 12.0, "B": 12.0, "C": 19.8}
SET_MONTHS_V3 = {"A": 31.0, "B": 32.0, "C": 31.7}

# 15分/4時間/日足ATRの中央値（eval/reports/20260823-cost-horizon.md の実測）
ATR_BY_HORIZON = {"15m": 0.00275, "1h": 0.0065, "4h": 0.0132, "1d": 0.0355}


def reconstruct_sigma(ev: float, win_pct: float, payoff: float | None) -> float | None:
    """勝率とペイオフから1回あたりの標準偏差を復元する。

    勝ち負けを2点の質量として扱う近似。実トレードと比べると σ を 2〜15% 低く
    出すので、Q = e/s は**楽観側**に振れる。フロンティアの形を見る用途には足りる。
    """
    if not payoff or payoff <= 0:
        return None
    w = win_pct / 100.0
    if not 0.0 < w < 1.0:
        return None
    denom = w * payoff - (1.0 - w)
    if abs(denom) < 1e-9:
        return None
    loss = ev / denom
    win = payoff * loss
    var = w * win**2 + (1.0 - w) * loss**2 - ev**2
    return float(np.sqrt(var)) if var > 0 else None


def load_records(reports_glob: str) -> pd.DataFrame:
    recs = []
    for path in sorted(glob.glob(reports_glob)):
        name = Path(path).stem
        try:
            rows = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(rows, list) or not rows or "logic_id" not in rows[0]:
            continue
        long_hist = "btc-long" in name or "btc-rate" in name
        table = SET_MONTHS_V3 if long_hist else SET_MONTHS_V1V2
        # v2 系（slow-sh01 / slow-delay / repro / oos）は6銘柄バスケット。
        # それ以外（edge / double-bottom / btc-*）は BTCUSDT 単独。
        # BTC単独に絞る指示があるので、混ぜたまま「実測」と呼ぶと読み違える。
        basket = any(k in name for k in ("slow-sh01", "slow-delay", "repro-sh01", "oos"))
        for r in rows:
            if not r.get("trades") or "set" not in r:
                continue
            months = table.get(r["set"], 12.0)
            sigma = reconstruct_sigma(
                r.get("avg_trade_pnl", 0.0), r.get("win_rate_pct", 0.0), r.get("payoff_ratio")
            )
            if sigma is None or sigma <= 0:
                continue
            recs.append(
                {
                    "logic_id": r["logic_id"],
                    "scope": "6銘柄" if basket else "BTC単独",
                    "family": r.get("family") or r.get("hypothesis_id") or "—",
                    "set": r["set"],
                    "trades": r["trades"],
                    "per_month": r["trades"] / months,
                    "ev": r["avg_trade_pnl"],
                    "sigma": sigma,
                    "q": r["avg_trade_pnl"] / sigma,
                }
            )
    return pd.DataFrame(recs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roi", type=float, default=120.0, help="月次ROI目標 (%)")
    ap.add_argument("--dd", type=float, default=20.0, help="最大DD上限 (%)")
    ap.add_argument("--max-leverage", type=float, default=3.0)
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--reports-glob", default="eval/reports/*set*.json")
    ap.add_argument("--out", default="eval/reports/20260824-target-feasibility.md")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    E = cfg.initial_equity
    T = args.roi / 100.0
    D = args.dd / 100.0
    need_nq2 = T / (2.0 * D)

    df = load_records(args.reports_glob)
    if df.empty:
        raise SystemExit("no usable records")

    L = [
        f"# 月次ROI {args.roi:.0f}% ／ 最大DD {args.dd:.0f}% は何を要求するか",
        "",
        f"元本 {E:.0f} USDT。月 {args.roi:.0f}% は月あたり **{T*E:.0f} USDT** の利益。",
        "",
        "## 1. サイズは答えにならない",
        "",
        "使う関係は3つ。",
        "",
        "```",
        "月次ROI = e × N / E          e = 1回のEV(USDT), N = 月の回数",
        "最大DD  ≈ s² / (2e)          s = 1回の標準偏差",
        "枠数    = N × H / 720        H = 平均保有時間(h)",
        "```",
        "",
        "上2つを割るとサイズが消えます。",
        "",
        "```",
        "ROI / DD = 2 × N × Q²        Q = e/s（1回あたりのシャープ）",
        "```",
        "",
        "ポジションを2倍にすると ROI も DD も2倍になるので、**比は動きません**。",
        f"つまり「月{args.roi:.0f}%をDD{args.dd:.0f}%以内で」の可否は、"
        "**レバレッジや証拠金では一切変わらず**、",
        "1回あたりの質 Q と月の回数 N だけで決まります。",
        "",
        f"**必要条件: N × Q² ≥ {need_nq2:.2f}**",
        "",
        "## 2. 必要な取引回数",
        "",
        "Q ごとに必要な N を出します。参考として、その N と Q を満たしたときの",
        "1回あたりEV（元本比）も併記します。",
        "",
        "| 1回の質 Q | 必要な回数/月 | 1回あたり必要EV | 月次シャープ |",
        "|---|---|---|---|",
    ]
    for q in (0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
        n_req = need_nq2 / q**2
        ev_req = T * E / n_req
        L.append(
            f"| {q:.2f} | **{n_req:,.0f}** | {ev_req:.2f} USDT ({100*ev_req/E:.2f}%) "
            f"| {q*np.sqrt(n_req):.2f} |"
        )

    # Q<0（EVマイナス）は二乗すると達成度が高く見えてしまうので除く。
    # n が小さい Q はばらつきの推定自体が信用できないので下限を引く。
    MIN_N = 20
    pos = df[(df["q"] > 0) & (df["trades"] >= MIN_N)].copy()
    pos["nq2"] = pos["per_month"] * pos["q"] ** 2
    best_q = pos["q"].max()
    best_row = pos.loc[pos["q"].idxmax()]
    L += [
        "",
        f"月次シャープが Q と N の組み合わせに関係なく {np.sqrt(need_nq2):.2f} で一定に",
        "なるのは偶然ではありません。ROI/DD 比を固定すると月次シャープも固定されます",
        f"（= √(ROI/2DD)）。年率換算で **{np.sqrt(need_nq2*12):.1f}**。",
        "**運用として実在する上位を大きく超える水準**です。",
        "",
        "## 3. 実測の Q はどのくらいか",
        "",
        "記録済み全ラン（変種×期間）で、勝率とペイオフから σ を復元して Q を出しました。",
        "復元は σ を 2〜15% 低く見積もるので、**下の Q は実際より良い数字**です。",
        "",
        f"EVがマイナスのランは Q が負で、二乗すると達成度が高く見えてしまうので除外。",
        f"n<{MIN_N} も、ばらつきの推定が信用できないので除外しました。",
        "",
        f"- 対象 {len(pos)} 件（全 {len(df)} 件から絞り込み）の Q: "
        f"最良 **{best_q:.3f}**（`{best_row['logic_id']}` set{best_row['set']}, "
        f"n={int(best_row['trades'])}）／中央値 {pos['q'].median():.3f}",
        "",
        "| 頻度帯（回/月） | EV+の記録数 | 最良Q | Q中央値 | N×Q²（最良） | 必要 | 到達 |",
        "|---|---|---|---|---|---|---|",
    ]
    bands = [(0, 5), (5, 10), (10, 25), (25, 50), (50, 100), (100, 10**9)]
    for lo, hi in bands:
        b = pos[(pos["per_month"] >= lo) & (pos["per_month"] < hi)]
        label = f"{lo}〜{hi}" if hi < 10**9 else f"{lo}+"
        n_all = len(df[(df["per_month"] >= lo) & (df["per_month"] < hi)])
        if b.empty:
            L.append(f"| {label} | 0 / {n_all} | — | — | — | {need_nq2:.2f} | × |")
            continue
        top = b.loc[b["nq2"].idxmax()]
        L.append(
            f"| {label} | {len(b)} / {n_all} | {top['q']:.3f} | {b['q'].median():.3f} "
            f"| **{top['nq2']:.3f}** | {need_nq2:.2f} "
            f"| {'○' if top['nq2'] >= need_nq2 else '×'} |"
        )

    best_nq2 = pos["nq2"].max()

    # 上の最良値は424件から取った最大なので、試行回数のぶん上振れしている。
    # 3期間すべてで EV+ を保った logic だけを残し、全期間をプールし直す。
    # これが「次の期間でも同じ数字が出る」と言える唯一の測り方。
    robust = []
    for (logic_id, scope), g in df.groupby(["logic_id", "scope"]):
        if len(g) < 3 or (g["ev"] <= 0).any():
            continue
        n_tot = g["trades"].sum()
        months = (g["trades"] / g["per_month"]).sum()
        ev_p = float((g["trades"] * g["ev"]).sum() / n_tot)
        var_p = float((g["trades"] * g["sigma"] ** 2).sum() / n_tot)
        sig_p = var_p**0.5
        if sig_p <= 0:
            continue
        q_p = ev_p / sig_p
        robust.append(
            {
                "logic_id": logic_id,
                "scope": scope,
                "n": int(n_tot),
                "per_month": n_tot / months,
                "ev": ev_p,
                "q": q_p,
                "t": q_p * n_tot**0.5,
                "nq2": (n_tot / months) * q_p**2,
            }
        )
    rob = pd.DataFrame(robust).sort_values("nq2", ascending=False)

    L += [
        "",
        f"ただし {best_nq2:.3f} は {len(pos)} 件から取った最大値なので、"
        "試行回数のぶん上振れしています。",
        "",
        "### 3期間すべてで EV+ を保ったものだけでプールし直す",
        "",
        "「次の期間でも同じ数字が出る」と言えるのはこちらだけです。",
        "3期間すべてで EV がプラスだった logic に絞り、全期間を1本にまとめました。",
        "",
        "| logic | 対象 | 合計n | 回/月 | プールEV | プールQ | t値 | N×Q² |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in rob.head(10).iterrows():
        L.append(
            f"| `{r['logic_id']}` | {r['scope']} | {r['n']} | {r['per_month']:.1f} "
            f"| {r['ev']:+.3f} | {r['q']:.3f} | {r['t']:+.2f} | **{r['nq2']:.3f}** |"
        )

    btc = rob[rob["scope"] == "BTC単独"]
    rob_best = float(rob["nq2"].max()) if not rob.empty else 0.0
    btc_best = float(btc["nq2"].max()) if not btc.empty else 0.0
    L += [
        "",
        "上位は6銘柄バスケット（v2）由来です。**BTC単独に絞る指示があるので、",
        "判定に使えるのは「BTC単独」の行だけ**です。",
        "",
        f"- 全体の最良: N×Q² = **{rob_best:.3f}** → 必要 {need_nq2:.2f} との差 "
        f"**{need_nq2/rob_best:.0f}倍**",
        f"- BTC単独の最良: N×Q² = **{btc_best:.3f}** → 差 **{need_nq2/btc_best:.0f}倍**"
        if btc_best > 0
        else "- BTC単独で3期間すべて EV+ を保ったものは無し",
        f"- 3期間すべてで EV+ を維持: {len(rob)} 本（うちBTC単独 {len(btc)} 本）",
        "",
        "",
        "BTC単独だけを並べ直すと:",
        "",
        "| logic | 合計n | 回/月 | プールEV | プールQ | t値 | N×Q² |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in btc.head(6).iterrows():
        L.append(
            f"| `{r['logic_id']}` | {r['n']} | {r['per_month']:.1f} | {r['ev']:+.3f} "
            f"| {r['q']:.3f} | {r['t']:+.2f} | **{r['nq2']:.3f}** |"
        )
    L += [
        "",
        "サイズでは埋まりません（1節）。Q を上げるか N を増やすかの2つしかなく、",
        "実測では両者が逆相関しています（上の頻度帯の表）。",
        "",
        "## 4. 保有時間の上限 — 「14時間」の出どころ",
        "",
        "前回の14.4時間は設計ではなく割り算です。**1枠しか持てないエンジンで**",
        "月50回撃つなら、720時間 ÷ 50 = 14.4時間しか1回に使えません。ロジックではなく制約です。",
        "",
        "同じ数字が、ROI目標とレバレッジ上限からも独立に出ます。",
        "必要レバは枠数（= N × H / 720）に比例するので、",
        "",
        "```",
        f"必要レバ = (N × H / 720) × (R / 損切り幅) / {E:.0f}",
        "```",
        "",
        f"N と R は1〜2節で決まるので、残る自由度は H と損切り幅だけ。"
        f"レバ {args.max_leverage:.0f}倍以内に収める上限を出します。",
        "",
        "| 損切り幅の目安 | 幅(%) | 必要枠数の上限 | H上限（N=75） | H上限（N=200） |",
        "|---|---|---|---|---|",
    ]
    # ここで使う 0.20 は EV/許容損失（R倍数）。Q = EV/標準偏差 とは別の量で、
    # σ が許容損失の 1.3〜1.6 倍なら 0.20R は Q ≈ 0.13〜0.15 に相当する。
    # 良好なシステムの目安として広く使われる水準。
    mu_r = 0.20
    q_assume = 0.20
    n_assume = need_nq2 / q_assume**2
    ev_assume = T * E / n_assume
    risk = ev_assume / mu_r
    for label, atr in ATR_BY_HORIZON.items():
        stop = 1.5 * atr
        notional = risk / stop
        slots_max = args.max_leverage * E / notional
        h75 = slots_max * 720 / 75
        h200 = slots_max * 720 / 200
        L.append(
            f"| {label}ATR × 1.5 | {stop*100:.2f}% | {slots_max:.2f} "
            f"| {h75:.1f}h | {h200:.1f}h |"
        )

    L += [
        "",
        f"（Q=0.20・N={n_assume:.0f} なら1回のEVは {ev_assume:.1f} USDT。"
        f"EVが許容損失の20%（=0.20R、良好なシステムの目安）とすると "
        f"許容損失は {risk:.1f} USDT。この 0.20R は Q=EV/標準偏差 とは別の量で、",
        f"σ が許容損失の1.3〜1.6倍なら Q≈0.13〜0.15 に相当します）",
        "",
        "**日足ATRで損切りを置くと、必要枠数が1枠を下回ります。** つまり月75回は",
        f"レバ{args.max_leverage:.0f}倍では成立しません。損切りを狭くすると枠は増やせますが、",
        "そのぶん往復コストが許容損失を食います（次節）。",
        "",
        "## 5. コストの床が同時に効く",
        "",
        "許容損失を固定してサイズを損切り幅で決めるので、コストの比率は幅だけで決まります。",
        "",
        "```",
        f"往復コスト / 許容損失 = {(cfg.fee_rate_per_side+cfg.slippage_pct_per_side)*2*100:.3f}% / 損切り幅",
        "```",
        "",
        "| 損切り幅の目安 | 幅(%) | コスト/許容損失 | 必要な粗EV（純EV 0.20R のとき） |",
        "|---|---|---|---|",
    ]
    cost_rate = (cfg.fee_rate_per_side + cfg.slippage_pct_per_side) * 2
    for label, atr in ATR_BY_HORIZON.items():
        stop = 1.5 * atr
        ratio = cost_rate / stop
        L.append(f"| {label}ATR × 1.5 | {stop*100:.2f}% | **{100*ratio:.1f}%** | {0.20+ratio:.2f}R |")

    q_rob = float(btc.loc[btc["nq2"].idxmax(), "q"]) if not btc.empty else best_q
    n_rob = float(btc.loc[btc["nq2"].idxmax(), "per_month"]) if not btc.empty else 0.0

    L += [
        "",
        "短く持つほどコストが許容損失を食い、長く持つほど枠が足りなくなります。",
        "**4時間ATR あたりが両方の妥協点**で、コストは許容損失の 7.6%、",
        "必要な粗EV は 0.28R です。",
        "",
        "## 6. 結論",
        "",
        f"- 月{args.roi:.0f}% ／ DD{args.dd:.0f}% は **N × Q² ≥ {need_nq2:.2f}** を要求する",
        f"- BTC単独・3期間プールでの最良は **{btc_best:.3f}**"
        f"（**{need_nq2/btc_best:.0f}倍**の差）"
        if btc_best > 0
        else "- BTC単独で3期間 EV+ を保ったものは無し",
        "- この差は**サイズ・レバレッジでは埋まらない**（1節）",
        f"- その Q ({q_rob:.2f}) を高頻度でも維持できたとして必要な回数は "
        f"**月 {need_nq2/q_rob**2:,.0f} 回**（実測は月 {n_rob:.1f} 回）",
        "- ただし実測では Q は頻度を上げると下がる（3節）ので、"
        "Q を保ったまま N だけ増やせる保証はない",
        "",
        f"目標を DD{args.dd:.0f}% のまま現実的な水準に置くなら、"
        "支えられる月次ROIは `ROI = 2 × DD × N × Q²`。",
        "",
        "| 回数/月 | Q=0.10 | Q=0.15 | Q=0.20 |",
        "|---|---|---|---|",
    ]
    for n in (50, 100, 200, 400):
        cells = [f"{2*D*n*q**2*100:.0f}%" for q in (0.10, 0.15, 0.20)]
        L.append(f"| {n} | " + " | ".join(cells) + " |")

    L += [
        "",
        f"月50回・Q=0.20（実測の最良）で **月{2*D*50*0.04*100:.0f}%** が上限の目安です。",
        "",
    ]

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
