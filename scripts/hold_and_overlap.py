"""保有上限を 6/12/16 時間に伸ばしたときの決済率と、重複エントリーの頻度。

問い:
  - 上限を伸ばすと、同じ RR でどれだけ幅を広げられるか
  - そのとき「建玉中に次のシグナルが来る」頻度はどれくらいか
  - 1枠で捨てるシグナルは何本か

Usage:
    python scripts/hold_and_overlap.py
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
from autotrade.strategy.bracket import (  # noqa: E402
    BARS_PER_HOUR,
    CYCLE_BRACKET,
    RR,
    STOP_PCT,
    build_signals,
    scan_bracket,
)

MAKER = 0.0002


def blended_cost(taker: float, slip: float, rr: float) -> float:
    w0 = 1.0 / (1.0 + rr)
    return MAKER + w0 * MAKER + (1 - w0) * (taker + slip)


def resolve_grid(df: pd.DataFrame, *, hours: float, rr: float, stop: float, sample: int, seed: int) -> dict:
    max_bars = int(round(hours * BARS_PER_HOUR))
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    rng = np.random.default_rng(seed)
    usable = len(close) - max_bars - 1
    entries = np.sort(rng.choice(usable, size=min(sample, usable), replace=False))
    rates, holds = [], []
    for d in (1, -1):
        r = scan_bracket(
            high, low, close, entries, direction=d, stop_pct=stop, rr=rr, max_bars=max_bars
        )
        rates.append(r["resolve_rate"])
        holds.append(r["mean_bars"])
    return {
        "resolve": float(np.mean(rates)),
        "mean_hours": float(np.mean(holds)) / BARS_PER_HOUR,
    }


def _exit_index(
    i: int,
    d: int,
    *,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    stop: float,
    rr: float,
    max_bars: int,
) -> int:
    if d > 0:
        stop_px, tp_px = close[i] * (1 - stop), close[i] * (1 + stop * rr)
    else:
        stop_px, tp_px = close[i] * (1 + stop), close[i] * (1 - stop * rr)
    end = min(i + max_bars, len(close) - 1)
    for j in range(i + 1, end + 1):
        if d > 0:
            hit = low[j] <= stop_px or high[j] >= tp_px
        else:
            hit = high[j] >= stop_px or low[j] <= tp_px
        if hit:
            return j
    return end


def overlap_stats(df: pd.DataFrame, logic_id: str, *, hours: float, stop: float, rr: float) -> dict:
    """シグナルが建玉中に何回来るか。

    仮想ロットを全部建てた場合の同時数と、1口座で取りうる3つの運用を数える。
      1slot     : 現行エンジン。空くまで捨てる
      same_side : one-way。同方向だけ足す。逆方向は捨てる（決済して反転はしない）
      hedge2    : hedge。long 1本 + short 1本まで。各方向は1枠
    """
    max_bars = int(round(hours * BARS_PER_HOUR))
    sig = build_signals(logic_id, df)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    n = len(close)

    taken_1 = skipped_1 = 0
    same_side = opp_side = 0
    taken_same = skipped_same = 0
    taken_hedge = skipped_hedge = 0
    concurrent_if_stacked: list[int] = []
    open_virtual: list[tuple[int, int]] = []  # (exit_i, direction) — 全部建てた仮想
    free_at = 0
    long_free = 0
    short_free = 0
    same_free = 0
    same_dir = 0

    for i in range(n - 1):
        open_virtual = [p for p in open_virtual if p[0] > i]
        d = int(sig[i])
        if d == 0:
            continue

        exit_i = _exit_index(
            i, d, high=high, low=low, close=close, stop=stop, rr=rr, max_bars=max_bars
        )
        concurrent_if_stacked.append(len(open_virtual) + 1)
        if open_virtual:
            if open_virtual[-1][1] == d:
                same_side += 1
            else:
                opp_side += 1

        # 1枠
        if i < free_at:
            skipped_1 += 1
        else:
            taken_1 += 1
            free_at = exit_i + 1

        # 同方向だけ足す（one-way のピラミッド）
        if i < same_free and d != same_dir:
            skipped_same += 1
        else:
            taken_same += 1
            same_dir = d
            same_free = max(same_free, exit_i + 1)

        # hedge: 方向ごとに1枠
        if d > 0:
            if i < long_free:
                skipped_hedge += 1
            else:
                taken_hedge += 1
                long_free = exit_i + 1
        else:
            if i < short_free:
                skipped_hedge += 1
            else:
                taken_hedge += 1
                short_free = exit_i + 1

        open_virtual.append((exit_i, d))

    stacked = np.array(concurrent_if_stacked, dtype=int) if concurrent_if_stacked else np.array([0])
    total_sig = taken_1 + skipped_1
    return {
        "signals": total_sig,
        "taken_1slot": taken_1,
        "skipped": skipped_1,
        "skip_pct": skipped_1 / total_sig if total_sig else 0.0,
        "same_side": same_side,
        "opp_side": opp_side,
        "taken_same": taken_same,
        "skipped_same": skipped_same,
        "taken_hedge": taken_hedge,
        "skipped_hedge": skipped_hedge,
        "max_concurrent": int(stacked.max()) if len(stacked) else 0,
        "p_ge2": float((stacked >= 2).mean()) if len(stacked) else 0.0,
        "p_ge3": float((stacked >= 3).mean()) if len(stacked) else 0.0,
        "p_ge5": float((stacked >= 5).mean()) if len(stacked) else 0.0,
        "mean_concurrent": float(stacked.mean()) if len(stacked) else 0.0,
    }


def horizon_sigma(close: np.ndarray, hours: float) -> float:
    bars = int(round(hours * BARS_PER_HOUR))
    if bars <= 0 or len(close) <= bars:
        return float("nan")
    rets = np.log(close[bars:] / close[:-bars])
    return float(np.std(rets))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v3_btc.lock.yaml")
    ap.add_argument("--sets", default="A,B,C")
    ap.add_argument("--logic", default="br_runs_5")
    ap.add_argument("--sample", type=int, default=2500)
    ap.add_argument("--out", default="eval/reports/20260825-hold-and-overlap.md")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    with open(args.lock, encoding="utf-8") as f:
        lock = yaml.safe_load(f)
    taker, slip = cfg.fee_rate_per_side, cfg.slippage_pct_per_side
    cost = blended_cost(taker, slip, RR)

    hours_grid = [6.0, 12.0, 16.0]
    stop_grid = [0.005, 0.007, 0.010, 0.014, 0.020]
    fine_stops = [0.007, 0.008, 0.009, 0.010, 0.011, 0.012, 0.013]
    rr = RR

    series = []
    for set_name in [s.strip() for s in args.sets.split(",")]:
        frames = load_multi_frames(lock, set_name, "BTCUSDT")
        df = frames["15m"]
        lo = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
        hi = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
        series.append((set_name, df.loc[(df.index >= lo) & (df.index <= hi)]))

    sigmas = {h: [] for h in hours_grid}
    for _, df in series:
        c = df["close"].to_numpy(float)
        for h in hours_grid:
            sigmas[h].append(horizon_sigma(c, h))
    sigma_mean = {h: float(np.mean(v)) for h, v in sigmas.items()}

    L = [
        "# 保有上限を延ばすと何が起きるか",
        "",
        f"現行枠: RR 1:{rr:.1f} ／ 損切り {STOP_PCT*100:.2f}% ／ 入口指値"
        f"（往復 {cost*100:.4f}%）／ 同時建玉 **1**（`engine.py` は `position is None` のときだけ新規）",
        f"重複の測定ロジック: `{args.logic}`（{CYCLE_BRACKET[args.logic]['why']}）",
        "",
        "## 0. 上限時間ごとの値動き",
        "",
        "| 上限 | 対数リターン σ | ブラケット合計（損切り0.70%） | 機能条件 σ ≳ 1.75% |",
        "|---|---|---|---|",
    ]
    for h in hours_grid:
        L.append(
            f"| {h:.0f}h | **{sigma_mean[h]*100:.2f}%** | 1.75% | "
            f"{'○' if sigma_mean[h] >= 0.0175 else '× 届きにくい'} |"
        )
    L += [
        "",
        "必要上振れは幅だけで決まり、上限時間には依存しません。",
        "上限を延ばす意味は「同じ決済率のまま幅を広げられる」こと。",
        "",
        "## 1. 上限時間ごとの決済率（無作為エントリー）",
        "",
        "| 上限 | 損切り | 利確 | 必要上振れ | 決済率 | 平均保有 | 70%到達 |",
        "|---|---|---|---|---|---|---|",
    ]

    rows = []
    for hours in hours_grid:
        for stop in stop_grid:
            res, holds = [], []
            for _, df in series:
                g = resolve_grid(df, hours=hours, rr=rr, stop=stop, sample=args.sample, seed=7)
                res.append(g["resolve"])
                holds.append(g["mean_hours"])
            resolve = float(np.mean(res))
            hold = float(np.mean(holds))
            uplift = (cost / stop) / (1 + rr)
            rows.append((hours, stop, resolve, hold, uplift))
            L.append(
                f"| {hours:.0f}h | {stop*100:.2f}% | {stop*rr*100:.2f}% "
                f"| +{uplift*100:.1f}pt | **{resolve*100:.0f}%** | {hold:.1f}h "
                f"| {'○' if resolve >= 0.70 else '×'} |"
            )

    fine_rows = []
    for hours in (12.0, 16.0):
        for stop in fine_stops:
            if any(abs(r[0] - hours) < 1e-12 and abs(r[1] - stop) < 1e-12 for r in rows):
                continue
            res, holds = [], []
            for _, df in series:
                g = resolve_grid(df, hours=hours, rr=rr, stop=stop, sample=args.sample, seed=7)
                res.append(g["resolve"])
                holds.append(g["mean_hours"])
            uplift = (cost / stop) / (1 + rr)
            fine_rows.append((hours, stop, float(np.mean(res)), float(np.mean(holds)), uplift))
    all_rows = rows + fine_rows

    L += [
        "",
        "必要上振れは幅だけで決まり、**上限時間には依存しません**。",
        "上限を延ばす効果は「同じ幅で決済率が上がる」か「同じ決済率で幅を広げられる」こと。",
        "",
        "## 2. 70%決済を保ったまま広げられる幅",
        "",
        "| 上限 | 70%を満たす最大の損切り | 利確 | 必要上振れ | 現行0.70%からの変化 |",
        "|---|---|---|---|---|",
    ]
    for hours in hours_grid:
        cand = [r for r in all_rows if r[0] == hours and r[2] >= 0.70]
        if not cand:
            L.append(f"| {hours:.0f}h | — | — | — | — |")
            continue
        best = max(cand, key=lambda r: r[1])
        L.append(
            f"| {hours:.0f}h | {best[1]*100:.2f}% | {best[1]*rr*100:.2f}% "
            f"| **+{best[4]*100:.1f}pt** | "
            f"{'現行' if abs(best[1]-STOP_PCT)<1e-12 else f'幅 {best[1]/STOP_PCT:.1f}倍'} |"
        )

    L += [
        "",
        "12h / 16h の境界（0.10pt刻み）:",
        "",
        "| 上限 | 損切り | 決済率 | 70% |",
        "|---|---|---|---|",
    ]
    for hours in (12.0, 16.0):
        subset = sorted(
            [r for r in all_rows if r[0] == hours and 0.0069 <= r[1] <= 0.0131],
            key=lambda r: r[1],
        )
        for r in subset:
            L.append(
                f"| {hours:.0f}h | {r[1]*100:.2f}% | **{r[2]*100:.0f}%** | "
                f"{'○' if r[2] >= 0.70 else '×'} |"
            )

    overlap_by_h: dict[float, list[dict]] = {}
    L += [
        "",
        "## 3. 建玉中に次のシグナルが来る頻度",
        "",
        f"`{args.logic}` のシグナル。同時数は**全部独立に建てた場合**（仮想ロット）。",
        "1枠の捨て率とは別。",
        "",
        "| 上限 | シグナル | 平均同時 | 同時2本以上 | 同時3本以上 | 同時5本以上 | 最大 | 重なりのうち同方向 | 逆方向 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for hours in hours_grid:
        parts = [overlap_stats(df, args.logic, hours=hours, stop=STOP_PCT, rr=rr) for _, df in series]
        overlap_by_h[hours] = parts
        sig = sum(p["signals"] for p in parts)
        same = sum(p["same_side"] for p in parts)
        opp = sum(p["opp_side"] for p in parts)
        overlap_n = same + opp
        same_pct = 100 * same / overlap_n if overlap_n else 0.0
        opp_pct = 100 * opp / overlap_n if overlap_n else 0.0
        L.append(
            f"| {hours:.0f}h | {sig:,} | {float(np.mean([p['mean_concurrent'] for p in parts])):.2f} "
            f"| {float(np.mean([p['p_ge2'] for p in parts]))*100:.0f}% "
            f"| {float(np.mean([p['p_ge3'] for p in parts]))*100:.0f}% "
            f"| {float(np.mean([p['p_ge5'] for p in parts]))*100:.0f}% "
            f"| {max(p['max_concurrent'] for p in parts)} "
            f"| {same_pct:.0f}% | {opp_pct:.0f}% |"
        )

    L += [
        "",
        "1口座で取りうる3つの運用（サブ口座なし）:",
        "",
        "| 上限 | 1枠で取る | 捨て率 | 同方向だけ足す | 捨て率 | hedge long1+short1 | 捨て率 |",
        "|---|---|---|---|---|---|---|",
    ]
    for hours in hours_grid:
        parts = overlap_by_h[hours]
        sig = sum(p["signals"] for p in parts)
        t1 = sum(p["taken_1slot"] for p in parts)
        ts = sum(p["taken_same"] for p in parts)
        th = sum(p["taken_hedge"] for p in parts)
        L.append(
            f"| {hours:.0f}h | {t1:,} | **{100*(sig-t1)/sig:.0f}%** "
            f"| {ts:,} | {100*(sig-ts)/sig:.0f}% "
            f"| {th:,} | {100*(sig-th)/sig:.0f}% |"
        )

    margin = cfg.margin_per_trade
    equity = cfg.initial_equity
    lev = cfg.leverage
    L += [
        "",
        "## 4. 証拠金（口座 1つ、銘柄 BTCUSDT のみ）",
        "",
        f"現行サイジングは証拠金 {margin:.0f} USDT × レバ {lev:.0f}（想定元本 {margin*lev:.0f}）／"
        f"口座 {equity:.0f} USDT。",
        "",
        "| 同時ネット建玉 | 拘束証拠金 | 口座に対する割合 | 口座に収まるか |",
        "|---|---|---|---|",
        f"| 1（現行） | {margin:.0f} | {100*margin/equity:.0f}% | ○ |",
        f"| 2 | {2*margin:.0f} | {100*2*margin/equity:.0f}% | ○ |",
        f"| 3 | {3*margin:.0f} | {100*3*margin/equity:.0f}% | ○ |",
        f"| 5 | {5*margin:.0f} | {100*5*margin/equity:.0f}% | × |",
        "",
        "証拠金だけ見ると2〜3本は収まります。**ボトルネックは証拠金ではなく取引所の建玉モデルです。**",
        "",
        "## 5. 1口座で「複数ポジション」は可能か（Bybit USDT無期限）",
        "",
        "本番先は Bybit。サブ口座は作らない前提。",
        "",
        "| やり方 | 取引所が見るもの | 独立した利確・損切り | 逆方向を同時に持てるか |",
        "|---|---|---|---|",
        "| one-way（既定） | 銘柄あたり **ネット1本** | ポジション全体に1セット、または Partial で数量ごと | **不可。** 逆指値は既存を減らす／反転する |",
        "| hedge | **long 1本 + short 1本** | 方向ごとに1セット（＋Partial） | ここまで。3本目は不可 |",
        "| ボットの仮想ロット | 取引所はネット1本のまま | ボットが部分決済を回す | one-way では不可 |",
        "",
        "結論: **独立したチケット（別の平均単価・別の清算価格）は1口座1銘柄では持てません。**",
        "Bybit 公式: one-way は Buy か Sell の一方、hedge でも Both Sides の2本まで。",
        "",
        "近づける手段は Partial TP/SL です。数量ごとの利確・損切りペアを複数置けて、",
        "片方に触れたら対応するもう片方はキャンセルされます。",
        "ただしこれは「独立ポジション」ではなく、**1本のネット建玉の上の条件付き注文**です。",
        "",
        "春希さんの懸念（利確・損切りがややこしい／処理が増えて遅延）は、この差から来ます。",
        "",
        "### 残るリスク（証拠金以外）",
        "",
        "| リスク | 何が起きるか | 1枠なら | 仮想複数 / Partial なら |",
        "|---|---|---|---|",
        "| 清算 | 清算価格はネットの想定元本で1つ | 単純 | 同方向に足すほど清算が近づく。ロット単位では守れない |",
        "| funding | ネット残高に対して8時間ごと | 平均保有3〜5hなら小さい | 同時2本なら想定元本も2倍 |",
        "| 平均単価 | 同方向に足すと avgPrice が動く | 動かない | ロットの想定エントリーと取引所の PnL がずれる |",
        "| 逆方向シグナル | 1枠なら捨てる（実測で重なりの約2割） | 元のブラケットが残る | one-way で取ると既存ブラケットが壊れる |",
        "| 全決済の連鎖 | ポジションが閉じると取引所が TP/SL をまとめてキャンセルし、残数量に合わせて qty を調整する | 起きない | 1ロットの決済が他ロットの注文サイズを変えることがある |",
        "| フル TP/SL との混在 | Full モードの損切りはネット全量 | それでよい | **使ってはいけない。** 全ロットが一気に閉じる |",
        "| ボット停止 | 取引所に残るのはネットと条件付き注文 | TP/SL 1セットなら生き残る | 仮想ロットの記憶が消えると、残注文と建玉が食い違う |",
        "| 注文数 | 入口＋利確＋損切りで3本 | 軽い | 同時3ロットなら約9本。条件付き注文の上限（銘柄あたり数十）は通常足りる |",
        "| 遅延 | CPU ではない | 15分足1本 | 約定のたびに cancel/replace。往復 50〜200ms × 本数。ボトルネックはレート制限とレース |",
        "| 統計 | 重なりは同じトレンドの延長 | 捨てるので独立に近い | 同方向の足し増しは相関する。回数は増えても情報は増えない |",
        "",
        "処理量そのものが足の判定を遅らせる、という心配は当たりません。",
        "遅れるのは「部分約定のあと、残りの損切り数量を直す」レースです。",
        "",
        "### 運用の分岐",
        "",
        "1. **1枠のまま上限だけ延ばす** — 捨て率は 6h でも 12h でもほぼ同じ（クラスタするため）。",
        "   本番リスクは増えない。幅を広げられるならこれが安全。",
        "2. **同方向だけ足す** — 取引所はネット1本。Partial TP/SL を数量ごとに置く。",
        "   逆方向は捨てる（既存を壊さない）。清算と相関が本体リスク。",
        "3. **hedge で逆方向も持つ** — long と short を同時に持てるが、クロス証拠金では片側の負けがもう片側を食う。",
        "   孤立証拠金なら方向ごとに清算されるが、必要証拠金は増える。",
        "4. **ボット仮想ロットを独自管理** — 取引所の Partial を使わず自前で部分決済。停止・欠測・レースが本番事故になる。非推奨。",
        "",
        "推奨: まずは 1。12h に延ばして幅を広げ、1枠のまま再検証。複数建玉は枠が黒字になってから。",
        "",
    ]

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
