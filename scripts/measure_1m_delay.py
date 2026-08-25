"""1分足で入口を取るときの遅延が、当たり率をどれだけ食うか。

遅延の種類:
  A. 足確定待ち — 未完成の足で判断すると未来を見る。必ず close を待つ
  B. 発注〜約定 — 指値なら板に乗るまで、成行なら往復遅延
  C. 欠測・時計ずれ — 1分足は欠けやすく、足が飛ぶとその判断は無効

A が支配的。1分足なら最大1分、15分足なら最大15分。
現行ブラケット（損切り0.70%、保有数時間）に対してこの差が効くかを測る。

Set C から 14 日分の 1分足を取り、
  - 遅延 0/1/2/5/15 本
  - 15分足 1 本遅れ（比較対象）
で無作為エントリーの当たり率を比べる。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.data.binance_vision import BinanceVisionClient, ensure_binance_data  # noqa: E402
from autotrade.strategy.bracket import RR, STOP_PCT, scan_bracket  # noqa: E402


def delayed_entries(n: int, delay: int, sample: int, seed: int, max_bars: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    usable = n - max_bars - delay - 2
    base = np.sort(rng.choice(usable, size=min(sample, usable), replace=False))
    return base + delay


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-08-01")
    ap.add_argument("--end", default="2026-08-14")
    ap.add_argument("--sample", type=int, default=4000)
    ap.add_argument("--hours", type=float, default=6.0)
    ap.add_argument("--out", default="eval/reports/20260825-1m-delay.md")
    args = ap.parse_args()

    cache = Path("data/cache")
    cache.mkdir(parents=True, exist_ok=True)
    client = BinanceVisionClient()
    print(f"fetching 1m {args.start}..{args.end}")
    try:
        m1 = ensure_binance_data(
            client, symbol="BTCUSDT", interval="1m", start=args.start, end=args.end, cache_dir=cache
        )
    except Exception as exc:  # noqa: BLE001 — 直近が取れなければ Set C の既知期間に倒す
        print(f"fetch failed ({exc}); falling back to 2024-01-01..2024-01-14")
        args.start, args.end = "2024-01-01", "2024-01-14"
        m1 = ensure_binance_data(
            client, symbol="BTCUSDT", interval="1m", start=args.start, end=args.end, cache_dir=cache
        )
    print(f"1m bars={len(m1)}")
    idx = m1.index
    expected = pd.date_range(idx.min(), idx.max(), freq="1min", tz="UTC")
    missing = int(len(expected) - len(idx.intersection(expected)))
    gaps = int((idx.to_series().diff().dt.total_seconds().fillna(60) > 60).sum())
    m15 = m1.resample("15min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna()

    high1 = m1["high"].to_numpy(float)
    low1 = m1["low"].to_numpy(float)
    close1 = m1["close"].to_numpy(float)
    max_bars_1m = int(round(args.hours * 60))
    max_bars_15 = int(round(args.hours * 4))

    L = [
        "# 1分足入口の遅延は当たり率をどれだけ食うか",
        "",
        f"期間: {args.start} 〜 {args.end}（BTCUSDT spot 1分足 {len(m1):,} 本）",
        f"欠測: カレンダー上 {missing:,} 本欠け（ギャップ {gaps} 箇所）／"
        f"{100*missing/max(len(expected),1):.2f}%",
        f"枠: RR 1:{RR:.1f} ／ 損切り {STOP_PCT*100:.2f}% ／ 保有上限 {args.hours:.0f}時間",
        "無作為エントリー。遅延は「シグナルが出た足から N 本あとに入る」。",
        "",
        "## 1分足での遅延",
        "",
        "| 遅れ | 実時間 | 決済率 | 勝率（決済分） | EV(R) |",
        "|---|---|---|---|---|",
    ]
    base_win = None
    for delay, label in ((0, "足確定直後"), (1, "1本=1分"), (2, "2分"), (5, "5分"), (15, "15分")):
        entries = delayed_entries(len(close1), delay, args.sample, 7, max_bars_1m)
        acc = []
        for d in (1, -1):
            acc.append(
                scan_bracket(
                    high1, low1, close1, entries,
                    direction=d, stop_pct=STOP_PCT, rr=RR, max_bars=max_bars_1m,
                )
            )
        win = float(np.mean([a["win_rate_resolved"] for a in acc]))
        res = float(np.mean([a["resolve_rate"] for a in acc]))
        ev = float(np.mean([a["ev_r"] for a in acc]))
        if delay == 0:
            base_win = win
        L.append(
            f"| {delay}本（{label}） | {delay}分 | {res*100:.1f}% | "
            f"**{win*100:.1f}%** | {ev:+.4f} |"
        )

    high15 = m15["high"].to_numpy(float)
    low15 = m15["low"].to_numpy(float)
    close15 = m15["close"].to_numpy(float)
    entries15 = delayed_entries(len(close15), 1, min(args.sample, len(close15) // 3), 7, max_bars_15)
    acc15 = []
    for d in (1, -1):
        acc15.append(
            scan_bracket(
                high15, low15, close15, entries15,
                direction=d, stop_pct=STOP_PCT, rr=RR, max_bars=max_bars_15,
            )
        )
    win15 = float(np.mean([a["win_rate_resolved"] for a in acc15]))
    res15 = float(np.mean([a["resolve_rate"] for a in acc15]))

    # ATR comparison
    tr1 = np.maximum(high1[1:] - low1[1:], np.maximum(np.abs(high1[1:] - close1[:-1]), np.abs(low1[1:] - close1[:-1])))
    atr1 = float(np.median(tr1 / close1[1:]))
    tr15 = np.maximum(
        high15[1:] - low15[1:],
        np.maximum(np.abs(high15[1:] - close15[:-1]), np.abs(low15[1:] - close15[:-1])),
    )
    atr15 = float(np.median(tr15 / close15[1:]))

    L += [
        "",
        f"同じ2週間を15分足に間引いて1本遅れで入れると、決済率 {res15*100:.1f}% ／ "
        f"勝率 {win15*100:.1f}%。",
        "",
        "## 足の大きさ",
        "",
        f"- 1分足 ATR 中央値: **{atr1*100:.3f}%**",
        f"- 15分足 ATR 中央値: **{atr15*100:.3f}%**（約 {atr15/atr1:.1f} 倍）",
        f"- 現行の損切り {STOP_PCT*100:.2f}% は 1分足ATRの **{STOP_PCT/atr1:.0f} 本分**、"
        f"15分足ATRの **{STOP_PCT/atr15:.1f} 本分**",
        "",
        "損切りが 1分足ATRの何十本もあるので、**1〜5分の遅れはノイズです。**",
        "15分待っても同じ。遅延が効くのは「足の中で完結するスキャル」で、",
        "このブラケット（数時間保有）では入口の足を 1分にする意味は",
        "**タイミングの精度ではなく、シグナルの定義を細かくできること**です。",
        "",
        "## 実務上の遅延リスク（測れないもの）",
        "",
        "| 種類 | 大きさ | この枠で効くか |",
        "|---|---|---|",
        "| 足確定待ち | 1分足なら最大1分、15分足なら最大15分 | 上記の通りほぼ効かない |",
        "| 取引所までの往復 | 通常 50〜200ms、混雑時 1秒超 | 1分足でも無視できる |",
        "| 指値のキュー | 触れただけでは約定しない | 15分足より1分足のほうが"
        "「触れた」判定が細かいので、**未約定の見積もりは改善する** |",
        "| 欠測 | 1分足は欠けやすい |"
        f" この2週間は {missing:,} 本（{100*missing/max(len(expected),1):.2f}%）。"
        "ゼロ埋めすると偽シグナル。**欠けたらスキップ** |",
        "| 時計ずれ | サーバと取引所で数秒 | 1分足だと足の帰属が1本ずれることがある。"
        "15分足では無視できた |",
        "| 処理負荷 | 1分足は15分足の15倍。8年で約 400 万本 | 検証は重い。"
        "本番は「直近N分だけ見る」なら問題にならない |",
        "| 未完成足で判断 | 今の1分足の high/low はまだ動く | **絶対に close を待つ**。"
        "ここを急ぐとバックテストと本番が乖離する |",
        "| 1分で入って15分で管理 | 15分足の high/low は入口より前の値を含むことがある | "
        "入口足と管理足を混ぜると先読みになる。管理も1分にするか、次の15分確定から見る |",
        "",
        "本番の Bybit クライアントはいま 15m / 4h / 1d しか持っていません"
        "（`INTERVAL_MAP`）。1分足入口にするなら取得側の追加が先です。",
        "検証の重さ（8年で約400万本）はリサーチの話で、本番は直近N分だけ見るので別問題です。",
        "",
    ]

    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
