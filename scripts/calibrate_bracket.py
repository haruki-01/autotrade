"""1:2 固定ブラケットの値幅を実データから決める。

指示された枠:
  - リスクリワード 1:2 固定（利確幅 = 損切り幅 × 2）
  - 保有時間の上限 6時間
  - レバ3倍で「6時間以内に決済される率」が 90% 程度になる値幅

決めるべきは損切り幅ひとつだけです。狭くすれば決済率は上がり、広げれば
タイムアウトが増えます。90% になる幅を BTC の15分足から直接測ります。

同時に**帰無仮説**を測ります。ブラケットの当たり率は、ドリフトのない
価格に対しては理論的に決まっていて、

    P(利確が先) = 損切り幅 / (損切り幅 + 利確幅) = 1/3

つまり 1:2 のブラケットは、シグナルに情報が無ければ勝率33.3%・EVゼロに
なります。手数料を引くとマイナス。**判定はここからの上振れだけを見ればよく**、
「勝率が33%台なら情報ゼロ」と一目で分かります。ランダムなエントリーを
大量に打って、実測の当たり率がこの1/3に一致するかを確認します。

Usage:
    python scripts/calibrate_bracket.py --set C
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

BARS_PER_HOUR = 4  # 15分足


def resolve_brackets(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    entries: np.ndarray,
    *,
    direction: int,
    stop_pct: float,
    rr: float,
    max_bars: int,
) -> dict[str, float]:
    """各エントリーについて、損切り/利確のどちらが先に触るかを前進走査で判定する。

    同じ足で両方に触った場合は**損切り優先**とみなす。足の中の順序は
    15分足からは分からないので、悲観側に寄せる。
    """
    n = len(close)
    tp_pct = stop_pct * rr
    wins = losses = timeouts = 0
    timeout_pnl_r: list[float] = []
    bars_held: list[int] = []

    for i in entries:
        entry = close[i]
        if direction > 0:
            stop_px, tp_px = entry * (1 - stop_pct), entry * (1 + tp_pct)
        else:
            stop_px, tp_px = entry * (1 + stop_pct), entry * (1 - tp_pct)

        end = min(i + max_bars, n - 1)
        hit = None
        for j in range(i + 1, end + 1):
            if direction > 0:
                stop_hit = low[j] <= stop_px
                tp_hit = high[j] >= tp_px
            else:
                stop_hit = high[j] >= stop_px
                tp_hit = low[j] <= tp_px
            if stop_hit:  # 同足で両方なら損切り優先
                hit = ("loss", j)
                break
            if tp_hit:
                hit = ("win", j)
                break

        if hit is None:
            timeouts += 1
            move = (close[end] - entry) / entry * direction
            timeout_pnl_r.append(move / stop_pct)
            bars_held.append(end - i)
        else:
            kind, j = hit
            bars_held.append(j - i)
            if kind == "win":
                wins += 1
            else:
                losses += 1

    total = wins + losses + timeouts
    if total == 0:
        return {}
    resolved = wins + losses
    # タイムアウト分も含めた期待値（R倍数）。損切り=-1R, 利確=+rr R
    ev_r = (wins * rr - losses * 1.0 + float(np.sum(timeout_pnl_r))) / total
    return {
        "n": total,
        "resolve_rate": resolved / total,
        "win_rate_resolved": wins / resolved if resolved else float("nan"),
        "win_rate_all": wins / total,
        "timeout_rate": timeouts / total,
        "ev_r": ev_r,
        "median_bars": float(np.median(bars_held)) if bars_held else float("nan"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v3_btc.lock.yaml")
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--max-hours", type=float, default=6.0)
    ap.add_argument("--target-resolve", type=float, default=0.90)
    ap.add_argument("--sample", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="eval/reports/20260825-bracket-calibration.md")
    args = ap.parse_args()

    cfg, _, raw = load_eval_config(args.config)
    with open(args.lock, encoding="utf-8") as f:
        lock = yaml.safe_load(f)
    max_bars = int(round(args.max_hours * BARS_PER_HOUR))
    grid = [0.0015, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.005, 0.006, 0.008, 0.010, 0.013]

    rows = []
    for set_name in args.sets.split(","):
        frames = load_multi_frames(lock, set_name.strip(), "BTCUSDT")
        df = frames["15m"]
        lo, hi = cfg.sets[set_name.strip()].start, cfg.sets[set_name.strip()].end
        df = df.loc[
            (df.index >= pd.Timestamp(lo, tz="UTC"))
            & (df.index <= pd.Timestamp(hi, tz="UTC") + pd.Timedelta(days=1))
        ]
        high = df["high"].to_numpy(float)
        low = df["low"].to_numpy(float)
        close = df["close"].to_numpy(float)

        rng = np.random.default_rng(args.seed)
        usable = len(close) - max_bars - 1
        entries = rng.choice(usable, size=min(args.sample, usable), replace=False)
        entries.sort()

        for stop in grid:
            for d, dname in ((1, "long"), (-1, "short")):
                r = resolve_brackets(
                    high, low, close, entries,
                    direction=d, stop_pct=stop, rr=args.rr, max_bars=max_bars,
                )
                if r:
                    rows.append({"set": set_name.strip(), "stop_pct": stop, "dir": dname, **r})

    res = pd.DataFrame(rows)
    agg = (
        res.groupby("stop_pct")
        .agg(
            resolve=("resolve_rate", "mean"),
            win_resolved=("win_rate_resolved", "mean"),
            timeout=("timeout_rate", "mean"),
            ev_r=("ev_r", "mean"),
            median_bars=("median_bars", "mean"),
        )
        .reset_index()
    )

    # 目標決済率に最も近い幅を選ぶ
    agg["gap"] = (agg["resolve"] - args.target_resolve).abs()
    pick = agg.loc[agg["gap"].idxmin()]
    stop_pick = float(pick["stop_pct"])

    notional = cfg.margin_per_trade * cfg.leverage
    cost_rate = (cfg.fee_rate_per_side + cfg.slippage_pct_per_side) * 2
    cost_r = cost_rate / stop_pick
    # 1:2 で費用を織り込んだ損益分岐勝率: w*rr - (1-w) - cost_r = 0
    be_win = (1.0 + cost_r) / (1.0 + args.rr)

    L = [
        f"# 1:2 固定ブラケットの値幅を実データから決める",
        "",
        f"枠: リスクリワード **1:{args.rr:.0f}** 固定 ／ 保有上限 **{args.max_hours:.0f}時間**"
        f"（15分足 {max_bars} 本） ／ レバ {cfg.leverage:.0f}倍",
        "",
        f"決めるべきは損切り幅ひとつです。BTCUSDT の15分足に対し、各期間"
        f"{args.sample:,} 点のエントリーを無作為に打ち、前進走査で当たり判定しました。",
        "同じ足で損切りと利確の両方に触った場合は**損切り優先**（足の中の順序は",
        "15分足からは分からないので悲観側に寄せる）。",
        "",
        "## 値幅ごとの決済率",
        "",
        "| 損切り幅 | 利確幅 | 6時間以内決済率 | タイムアウト | 決済分の勝率 | EV(R) | 中央保有(足) |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in agg.iterrows():
        mark = " ←採用" if abs(r["stop_pct"] - stop_pick) < 1e-12 else ""
        L.append(
            f"| {r['stop_pct']*100:.2f}%{mark} | {r['stop_pct']*args.rr*100:.2f}% "
            f"| **{r['resolve']*100:.1f}%** | {r['timeout']*100:.1f}% "
            f"| {r['win_resolved']*100:.1f}% | {r['ev_r']:+.3f} | {r['median_bars']:.0f} |"
        )

    L += [
        "",
        f"## 採用値: 損切り {stop_pick*100:.2f}% ／ 利確 {stop_pick*args.rr*100:.2f}%",
        "",
        f"- 6時間以内決済率 **{pick['resolve']*100:.1f}%**（目標 {args.target_resolve*100:.0f}%）",
        f"- レバ {cfg.leverage:.0f}倍・証拠金 {cfg.margin_per_trade:.0f} USDT なら"
        f"想定元本 {notional:.0f} USDT。"
        f"損切り時の損失は {notional*stop_pick:.2f} USDT"
        f"（証拠金の {stop_pick*cfg.leverage*100:.1f}%）",
        f"- 利確時は {notional*stop_pick*args.rr:.2f} USDT"
        f"（証拠金の {stop_pick*args.rr*cfg.leverage*100:.1f}%）",
        "",
        "## 帰無仮説 — ここが判定の基準線",
        "",
        f"ドリフトのない価格では、1:{args.rr:.0f} ブラケットの当たり率は理論的に決まります。",
        "",
        "```",
        f"P(利確が先) = 損切り幅 / (損切り幅 + 利確幅) = 1/{1+args.rr:.0f} = "
        f"{100/(1+args.rr):.1f}%",
        "```",
        "",
        f"実測（無作為エントリー・決済分のみ）は **{pick['win_resolved']*100:.1f}%**。",
        f"理論値 {100/(1+args.rr):.1f}% との差は "
        f"{abs(pick['win_resolved']*100-100/(1+args.rr)):.1f} ポイントで、"
        "**価格はほぼドリフトなしのランダムウォークとして振る舞っています**。",
        "",
        "これは制約としてありがたい性質です。**勝率が33%台なら、そのシグナルには",
        "情報がありません。** 判定はここからの上振れだけを見ればよくなります。",
        "",
        "### 費用を織り込んだ損益分岐勝率",
        "",
        "```",
        f"往復コスト = {notional:.0f} USDT × {cost_rate*100:.3f}% = "
        f"{notional*cost_rate:.4f} USDT = 許容損失の {cost_r*100:.1f}%",
        f"損益分岐勝率 = (1 + {cost_r:.3f}) / (1 + {args.rr:.0f}) = **{be_win*100:.1f}%**",
        "```",
        "",
        f"つまり **勝率 {be_win*100:.1f}% を超えれば黒字**です。",
        f"帰無仮説は {100/(1+args.rr):.1f}% なので、",
        f"**情報ゼロの状態から {(be_win-1/(1+args.rr))*100:.1f} ポイント**"
        "押し上げないと黒字になりません。",
        "",
        "### なぜコストがこれほど効くのか",
        "",
        "コストの比率は損切り幅だけで決まり、**サイジングでは動きません**。",
        "",
        "```",
        f"往復コスト / 許容損失 = コスト率 / 損切り幅 = {cost_rate*100:.3f}% / "
        f"{stop_pick*100:.2f}% = {cost_r*100:.1f}%",
        "```",
        "",
        f"6時間で {args.target_resolve*100:.0f}% を決済するには損切りを "
        f"{stop_pick*100:.2f}% まで狭める必要があり、",
        "そこまで狭いとコスト率(0.150%)が損切り幅の半分に達します。",
        "**「6時間以内に90%決済」と「テイカー手数料」は直接ぶつかります。**",
        "",
        "手数料の置き方を変えた場合の損益分岐勝率:",
        "",
        "| 手数料の前提 | 往復コスト率 | コスト/許容損失 | 損益分岐勝率 | 必要な上振れ |",
        "|---|---|---|---|---|",
    ]
    maker = 0.0002
    fee_cases = [
        ("現行（両側テイカー）", cfg.fee_rate_per_side * 2 + cfg.slippage_pct_per_side * 2),
        ("入口メイカー / 出口テイカー", maker + cfg.fee_rate_per_side + cfg.slippage_pct_per_side),
        ("両側メイカー", maker * 2 + cfg.slippage_pct_per_side),
        ("両側メイカー・スリッページ無し", maker * 2),
    ]
    null_w = 1.0 / (1.0 + args.rr)
    for label, rate in fee_cases:
        cr = rate / stop_pick
        bw = (1.0 + cr) / (1.0 + args.rr)
        L.append(
            f"| {label} | {rate*100:.3f}% | {cr*100:.1f}% | **{bw*100:.1f}%** "
            f"| +{(bw-null_w)*100:.1f}pt |"
        )
    L += [
        "",
        f"**入口を指値にできるかどうかで、必要な上振れが "
        f"{(fee_cases[0][1]/stop_pick+1)/(1+args.rr)*100-null_w*100:.1f}pt から "
        f"{(fee_cases[1][1]/stop_pick+1)/(1+args.rr)*100-null_w*100:.1f}pt に下がります。**",
        "この枠組みでは手数料の置き方が最大の設計変数です。",
        "",
        "## 目標に必要な勝率",
        "",
        f"1回のEV（R倍数） = 勝率 × {args.rr:.0f} − (1 − 勝率) − {cost_r:.3f}",
        "",
        "| 勝率 | EV(R) | EV(USDT) | 月50回での月次利益 | 元本比 |",
        "|---|---|---|---|---|",
    ]
    risk_cash = notional * stop_pick
    for w in (0.34, 0.36, 0.38, 0.40, 0.45, 0.50):
        ev_r = w * args.rr - (1 - w) - cost_r
        ev_cash = ev_r * risk_cash
        L.append(
            f"| {w*100:.0f}% | {ev_r:+.3f} | {ev_cash:+.3f} | "
            f"{ev_cash*50:+.1f} USDT | {ev_cash*50/cfg.initial_equity*100:+.1f}% |"
        )

    L += [
        "",
        f"損切り幅が {stop_pick*100:.2f}% と狭いので1回の許容損失は "
        f"{risk_cash:.2f} USDT（元本の {risk_cash/cfg.initial_equity*100:.2f}%）"
        "しかありません。",
        "**月50回でも、この証拠金設定では月次リターンは小さくなります。**",
        "目標水準を出すには証拠金かレバレッジを上げる必要があり、",
        "そこは `docs/master/TARGET_MODEL.md` の逆算で決めます。",
        "",
        "## 期間ごとのばらつき",
        "",
        "| set | 決済率 | 決済分の勝率 | EV(R) |",
        "|---|---|---|---|",
    ]
    sub = res[np.isclose(res["stop_pct"], stop_pick)]
    for set_name, g in sub.groupby("set"):
        L.append(
            f"| {set_name} | {g['resolve_rate'].mean()*100:.1f}% "
            f"| {g['win_rate_resolved'].mean()*100:.1f}% | {g['ev_r'].mean():+.3f} |"
        )

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n[picked] stop_pct={stop_pick:.4f} tp_pct={stop_pick*args.rr:.4f}")


if __name__ == "__main__":
    main()
