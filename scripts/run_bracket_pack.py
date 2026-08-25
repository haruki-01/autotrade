"""固定ブラケット（1:2・保有上限6時間）で15分足のエントリー条件を検証する。

値幅・RR・保有上限が全条件で共通なので、専用の前進走査で足りる。エンジンを
通さないのは、この枠だと約定結果が「損切り / 利確 / 6時間タイムアウト」の
3通りしか無く、損益がブラケットから解析的に決まるため。

判定は勝率ひとつ。ドリフトのない価格に対する 1:2 ブラケットの当たり率は
1/3 に決まるので、

    勝率 <= 33.3%  → シグナルに情報が無い
    勝率 >= 損益分岐 → 黒字（損益分岐はコスト率/損切り幅で決まる）

という2本の線で読める。対照（無作為エントリー）を同じ計測系で回して、
基準線が理論値どおり出ることも毎回確認する。

Usage:
    python scripts/run_bracket_pack.py --set C
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.eval.multi import load_multi_derivatives, load_multi_frames  # noqa: E402
from autotrade.strategy.bracket import (  # noqa: E402
    BARS_PER_HOUR,
    BARS_PER_HOUR_1M,
    CYCLE_BRACKET,
    MAX_HOURS,
    RR,
    STOP_PCT,
    build_signals,
    cycle_bracket_1m,
)


def run_bracket(
    df: pd.DataFrame,
    signals: np.ndarray,
    *,
    stop_pct: float,
    rr: float,
    max_bars: int,
    cost_rate: float,
    notional: float,
    slots: int = 1,
) -> dict:
    """シグナルを順に処理し、重複しない範囲でブラケットを解決する。

    ``slots`` はエンジンと同じ「同時に持てる建玉数」。既定は1で、現行の
    ``engine.py`` と同じ制約にしてある。
    """
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    close = df["close"].to_numpy(float)
    n = len(close)
    risk_cash = notional * stop_pct
    cost_cash = notional * cost_rate

    trades: list[dict] = []
    free_at = 0  # slots=1 前提。次に入れる足のインデックス

    for i in range(n - 1):
        d = int(signals[i])
        if d == 0 or i < free_at:
            continue
        entry = close[i]
        if d > 0:
            stop_px = entry * (1 - stop_pct)
            tp_px = entry * (1 + stop_pct * rr)
        else:
            stop_px = entry * (1 + stop_pct)
            tp_px = entry * (1 - stop_pct * rr)

        end = min(i + max_bars, n - 1)
        outcome = None
        for j in range(i + 1, end + 1):
            if d > 0:
                hit_stop = low[j] <= stop_px
                hit_tp = high[j] >= tp_px
            else:
                hit_stop = high[j] >= stop_px
                hit_tp = low[j] <= tp_px
            if hit_stop:  # 同足で両方なら損切り優先（悲観側）
                outcome = ("loss", j, -1.0)
                break
            if hit_tp:
                outcome = ("win", j, rr)
                break
        if outcome is None:
            move = (close[end] - entry) / entry * d
            outcome = ("timeout", end, move / stop_pct)

        kind, j, r_mult = outcome
        pnl = r_mult * risk_cash - cost_cash
        trades.append(
            {
                "entry_i": i,
                "exit_i": j,
                "dir": d,
                "kind": kind,
                "r_mult": r_mult,
                "pnl": pnl,
                "bars": j - i,
            }
        )
        free_at = j + 1

    if not trades:
        return {"trades": 0}

    t = pd.DataFrame(trades)
    n_t = len(t)
    wins = int((t["kind"] == "win").sum())
    losses = int((t["kind"] == "loss").sum())
    timeouts = int((t["kind"] == "timeout").sum())
    resolved = wins + losses
    pnl = t["pnl"].to_numpy()
    ev = float(pnl.mean())
    sd = float(pnl.std(ddof=1)) if n_t > 1 else float("nan")

    # 勝率が 1/3 から上振れているかの検定。分母はタイムアウトを除いた決済分。
    p0 = 1.0 / (1.0 + rr)
    if resolved > 0:
        p_hat = wins / resolved
        se = np.sqrt(p0 * (1 - p0) / resolved)
        z_win = (p_hat - p0) / se
    else:
        p_hat, z_win = float("nan"), float("nan")

    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.concatenate([[0.0], equity]))
    dd = float(np.max(peak - np.concatenate([[0.0], equity])))

    return {
        "trades": n_t,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "resolve_rate": resolved / n_t,
        "win_rate_resolved": p_hat,
        "z_vs_null": float(z_win),
        "ev_usdt": ev,
        "ev_r": float(t["r_mult"].mean()),
        "sd_usdt": sd,
        "t_stat": float(ev / sd * np.sqrt(n_t)) if sd and sd > 0 else float("nan"),
        "q": float(ev / sd) if sd and sd > 0 else float("nan"),
        "total_pnl": float(pnl.sum()),
        "max_dd_usdt": dd,
        "median_bars": float(t["bars"].median()),
        "long_share": float((t["dir"] > 0).mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/eval_v3_btc.yaml")
    ap.add_argument("--lock", default="eval/locks/eval_v3_btc.lock.yaml")
    ap.add_argument("--set", required=True)
    ap.add_argument("--logics", default="")
    ap.add_argument("--interval", default="15m", choices=("15m", "1m"))
    ap.add_argument("--ohlcv-only", action="store_true", help="派生データ条件を外す")
    ap.add_argument("--maker-entry", action="store_true", help="入口をメイカーとして計算")
    ap.add_argument("--stop", type=float, default=None, help="損切り幅（既定は bracket.py の値）")
    ap.add_argument("--rr", type=float, default=None, help="リスクリワード比")
    ap.add_argument("--tag", default="bracket")
    args = ap.parse_args()

    cfg, _, _ = load_eval_config(args.config)
    with open(args.lock, encoding="utf-8") as f:
        lock = yaml.safe_load(f)

    if args.interval == "1m":
        entry = lock["datasets"][args.set]["symbols"]["BTCUSDT"]
        path_str = next(iter(entry["files"]))
        from autotrade.data.bybit import load_ohlcv

        df = load_ohlcv(Path(path_str))
        cycle = cycle_bracket_1m()
        bars_per_hour = BARS_PER_HOUR_1M
    else:
        frames = load_multi_frames(lock, args.set, "BTCUSDT")
        df = frames["15m"]
        cycle = CYCLE_BRACKET
        bars_per_hour = BARS_PER_HOUR

    lo = pd.Timestamp(cfg.sets[args.set].start, tz="UTC")
    hi = pd.Timestamp(cfg.sets[args.set].end, tz="UTC") + pd.Timedelta(days=1)
    df = df.loc[(df.index >= lo) & (df.index <= hi)]
    months = (hi - lo).days / 30.4375

    ids = [s.strip() for s in args.logics.split(",") if s.strip()] or list(cycle)
    if args.ohlcv_only or args.interval == "1m":
        ids = [i for i in ids if not cycle.get(i, {}).get("needs_deriv")]
    needs_deriv = any(cycle.get(i, {}).get("needs_deriv") for i in ids)
    if needs_deriv:
        deriv = None
        try:
            deriv = load_multi_derivatives(lock, args.set, "BTCUSDT", df.index)
        except (RuntimeError, KeyError, TypeError):
            from autotrade.data.binance_derivatives import load_context

            ctx = load_context(
                df.index,
                symbol="BTCUSDT",
                start=cfg.sets[args.set].start,
                end=cfg.sets[args.set].end,
            )
            deriv = ctx.frame
        if deriv is not None and not deriv.empty:
            df = df.join(deriv, how="left", rsuffix="_d")
            print(f"derivatives joined: {list(deriv.columns)}")
        else:
            ids = [i for i in ids if not cycle.get(i, {}).get("needs_deriv")]
            print("derivatives unavailable — skipping needs_deriv logics")

    stop_pct = args.stop if args.stop is not None else STOP_PCT
    rr = args.rr if args.rr is not None else RR
    notional = cfg.margin_per_trade * cfg.leverage
    if args.maker_entry:
        # 入口は指値でメイカー。出口は利確だけメイカーで、損切りは成行に
        # せざるを得ない（指値だと急落で約定しない）。スリッページも
        # テイカー側の脚にだけ乗せる。
        maker, taker = 0.0002, cfg.fee_rate_per_side
        slip = cfg.slippage_pct_per_side
        w0 = 1.0 / (1.0 + rr)
        cost_rate = maker + w0 * maker + (1 - w0) * (taker + slip)
    else:
        cost_rate = (cfg.fee_rate_per_side + cfg.slippage_pct_per_side) * 2
    max_bars = int(round(MAX_HOURS * bars_per_hour))
    cost_r = cost_rate / stop_pct
    be_win = (1.0 + cost_r) / (1.0 + rr)

    rows = []
    for k, logic_id in enumerate(ids, 1):
        sig = build_signals(logic_id, df, cycle=cycle)
        r = run_bracket(
            df, sig,
            stop_pct=stop_pct, rr=rr, max_bars=max_bars,
            cost_rate=cost_rate, notional=notional,
        )
        if not r.get("trades"):
            print(f"[{k:3d}/{len(ids)}] {logic_id:22s} シグナルなし")
            continue
        r["logic_id"] = logic_id
        r["why"] = cycle[logic_id]["why"]
        r["set"] = args.set
        r["per_month"] = r["trades"] / months
        r["beats_null"] = r["win_rate_resolved"] > 1.0 / (1.0 + rr)
        r["profitable"] = r["ev_usdt"] > 0 and r["trades"] >= cfg.min_trades
        rows.append(r)
        print(
            f"[{k:3d}/{len(ids)}] {logic_id:22s} "
            f"n={r['trades']:5d} ({r['per_month']:5.1f}/月) "
            f"勝率={r['win_rate_resolved']*100:5.1f}% z={r['z_vs_null']:+5.2f} "
            f"EV={r['ev_usdt']:+.4f} t={r['t_stat']:+5.2f}"
        )

    res = pd.DataFrame(rows).sort_values("z_vs_null", ascending=False)
    stamp = f"eval/reports/20260825-{args.tag}-set{args.set}"
    Path(stamp + ".json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    fee_label = "入口メイカー/出口テイカー" if args.maker_entry else "両側テイカー"
    L = [
        f"# 固定ブラケット検証 — Set {args.set}",
        "",
        f"BTCUSDT {args.interval} ／ 損切り **{stop_pct*100:.2f}%** ／ 利確 "
        f"**{stop_pct*rr*100:.2f}%**（1:{rr:.1f}）／ 保有上限 **{MAX_HOURS:.0f}時間** ／ "
        f"同時建玉 1",
        f"期間: {cfg.sets[args.set].start} 〜 {cfg.sets[args.set].end}（{months:.1f}ヶ月）",
        f"手数料前提: {fee_label}（往復 {cost_rate*100:.3f}% = 許容損失の {cost_r*100:.1f}%）",
        "",
        "## 判定の2本の線",
        "",
        f"- **帰無仮説 {100/(1+rr):.1f}%** — ドリフトのない価格での 1:{rr:.1f} ブラケット当たり率。"
        "これ以下なら情報ゼロ",
        f"- **損益分岐 {be_win*100:.1f}%** — 費用を引いて黒字になる勝率",
        f"- 差は **{(be_win-1/(1+rr))*100:.1f} ポイント**。ここを超える条件を探している",
        "",
        "## 結果（勝率の上振れ順）",
        "",
        f"| logic | 狙い | n | 回/月 | 決済率 | 勝率 | z(vs {100/(1+rr):.1f}%) | EV(USDT) | t値 | 判定 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in res.iterrows():
        if r["ev_usdt"] > 0 and r["trades"] >= cfg.min_trades:
            verdict = "黒字"
        elif r["ev_usdt"] > 0:
            verdict = "黒字だがn不足"
        elif r["win_rate_resolved"] > 1.0 / (1.0 + rr):
            verdict = "情報あり/赤字"
        else:
            verdict = "情報なし"
        L.append(
            f"| `{r['logic_id']}` | {r['why']} | {r['trades']} | {r['per_month']:.1f} "
            f"| {r['resolve_rate']*100:.1f}% | **{r['win_rate_resolved']*100:.1f}%** "
            f"| {r['z_vs_null']:+.2f} | {r['ev_usdt']:+.4f} | {r['t_stat']:+.2f} | {verdict} |"
        )

    ctrl = res[res["logic_id"].str.startswith("br_random")]
    L += [
        "",
        "## 対照の確認",
        "",
        "無作為エントリーが理論値どおりになるかで、計測系そのものを検算します。",
        "",
    ]
    for _, r in ctrl.iterrows():
        L.append(
            f"- `{r['logic_id']}`: 勝率 {r['win_rate_resolved']*100:.1f}%"
            f"（理論 {100/(1+rr):.1f}%、z={r['z_vs_null']:+.2f}）、n={r['trades']}"
        )

    beats = res[res["win_rate_resolved"] > 1.0 / (1.0 + rr)]
    profit = res[(res["ev_usdt"] > 0) & (res["trades"] >= cfg.min_trades)]
    profit_tiny = res[(res["ev_usdt"] > 0) & (res["trades"] < cfg.min_trades)]
    L += [
        "",
        "## まとめ",
        "",
        f"- 検証した条件: **{len(res)}**",
        f"- 帰無仮説（{100/(1+rr):.1f}%）を上回った: **{len(beats)}**",
        f"- z ≥ 2（偶然では説明しにくい）: **{int((res['z_vs_null'] >= 2).sum())}**",
        f"- 費用後に黒字（n≥{cfg.min_trades}）: **{len(profit)}**",
        f"- 黒字だがサンプル不足: **{len(profit_tiny)}**",
        f"- 月50回以上撃てた: **{int((res['per_month'] >= 50).sum())}**",
        "",
    ]
    Path(stamp + ".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[-9:]))


if __name__ == "__main__":
    main()
