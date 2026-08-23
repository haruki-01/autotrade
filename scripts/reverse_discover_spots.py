#!/usr/bin/env python3
"""Reverse-discover trade-spot candidates from historical OHLCV.

Modes:
  1d grid + success profile (legacy)
  4h grid + session/hour features
  big-move reverse profile (label extreme forward moves, profile antecedents)

Discovery period only — does NOT score holdout / formal eval.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "hypothesis" / "spots" / "DISCOVERED_FROM_DATA.md"

DISCOVERY_1D = ROOT / "data/cache/BTCUSDT_binance_spot_1d_2022-05-26_2023-12-31.csv"
DISCOVERY_4H = ROOT / "data/cache/BTCUSDT_binance_spot_4h_2022-05-26_2023-12-31.csv"
HOLDOUT_NOTE = "2024-01-01 → 2024-12-31 (formal eval only; not used here)"

COST = 0.002


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def summarize(mask: pd.Series, fwd: pd.Series, name: str) -> dict:
    sub = fwd[mask].dropna()
    n = int(sub.shape[0])
    if n == 0:
        return {"name": name, "n": 0}
    return {
        "name": name,
        "n": n,
        "mean": float(sub.mean()),
        "median": float(sub.median()),
        "beat_cost_rate": float((sub > COST).mean()),
        "p75": float(sub.quantile(0.75)),
    }


def add_common_features(df: pd.DataFrame, *, h_fwd: int, hh: int = 20) -> pd.DataFrame:
    c = df["close"].astype(float)
    hi = df["high"].astype(float)
    lo = df["low"].astype(float)
    o = df["open"].astype(float)
    out = pd.DataFrame({"timestamp": df["timestamp"]})
    out["close"] = c
    out["ret_1"] = c.pct_change()
    out["fwd_ret"] = c.shift(-h_fwd) / c - 1.0
    # max favorable excursion proxy over horizon (long): peak high / close - 1
    fut_max = hi.iloc[::-1].rolling(h_fwd, min_periods=1).max().iloc[::-1].shift(-1)
    out["fwd_mfe"] = fut_max / c - 1.0

    out["sma20"] = c.rolling(20).mean()
    out["sma50"] = c.rolling(50).mean()
    out["above_sma50"] = c > out["sma50"]
    out["sma50_up"] = out["sma50"] > out["sma50"].shift(5)

    prev = c.shift(1)
    tr = pd.concat([(hi - lo), (hi - prev).abs(), (lo - prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    out["atr_pct"] = atr / c
    out["atr_sma20"] = out["atr_pct"].rolling(20).mean()
    out["compressed"] = out["atr_pct"] < out["atr_sma20"] * 0.75
    out["expanded"] = out["atr_pct"] > out["atr_sma20"] * 1.25

    out["hh"] = hi.rolling(hh).max()
    out["ll"] = lo.rolling(hh).min()
    rng = (out["hh"] - out["ll"]).replace(0, np.nan)
    out["pos"] = (c - out["ll"]) / rng
    out["near_high"] = out["pos"] > 0.85
    out["near_low"] = out["pos"] < 0.15
    out["break_hh"] = c > out["hh"].shift(1)
    out["break_ll"] = c < out["ll"].shift(1)
    out["up_sig"] = out["break_hh"] & ~out["break_hh"].shift(1).fillna(False)

    out["dd_from_hh"] = c / out["hh"] - 1.0
    out["shallow_pb"] = (out["dd_from_hh"] > -0.08) & (out["dd_from_hh"] < -0.02)
    out["half_pb"] = (out["dd_from_hh"] > -0.06) & (out["dd_from_hh"] < -0.03)
    out["bull"] = c > o

    ts = pd.to_datetime(out["timestamp"], utc=True)
    out["weekday"] = ts.dt.weekday
    out["hour_utc"] = ts.dt.hour
    # Thick sessions (approx): London 7–16, NY overlap 13–16 UTC
    out["london"] = out["hour_utc"].between(7, 15)
    out["ny_overlap"] = out["hour_utc"].between(13, 16)
    out["asia_thin"] = out["hour_utc"].between(0, 6)
    return out


def table_lines(rows: list[dict], *, min_n: int) -> list[str]:
    ranked = [r for r in rows if r.get("n", 0) >= min_n]
    ranked.sort(key=lambda r: r.get("mean", -999), reverse=True)
    lines = [
        "| 条件 | n | mean | median | beat cost |",
        "|------|---|------|--------|-----------|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['name']}` | {r['n']} | {r['mean']:.2%} | {r['median']:.2%} | "
            f"{r['beat_cost_rate']:.1%} |"
        )
    thin = [r for r in rows if 0 < r.get("n", 0) < min_n]
    if thin:
        lines.append("")
        lines.append(f"n<{min_n}（参考・昇格慎重）:")
        for r in sorted(thin, key=lambda x: -x.get("mean", -999))[:8]:
            lines.append(f"- `{r['name']}`: n={r['n']}, mean={r.get('mean', float('nan')):.2%}")
    return lines


def run_1d(lines: list[str]) -> None:
    H, TAU = 10, 0.02
    raw = load_csv(DISCOVERY_1D)
    f = add_common_features(raw, h_fwd=H, hh=20)
    fwd = f["fwd_ret"]
    base = summarize(fwd.notna(), fwd, "ALL_1D")
    candidates = [
        ("D_near_high_expanded", f["near_high"] & f["expanded"] & f["above_sma50"]),
        ("D_break_hh_not_compressed", f["break_hh"] & (~f["compressed"]) & f["above_sma50"]),
        ("D_up_sig_expanded", f["up_sig"] & f["expanded"] & f["above_sma50"]),
        ("D_half_pb_uptrend", f["half_pb"] & f["above_sma50"] & f["sma50_up"]),
        ("D_shallow_pb_uptrend", f["shallow_pb"] & f["above_sma50"] & f["sma50_up"]),
        ("D_compress_near_high", f["compressed"] & f["near_high"] & f["above_sma50"]),
    ]
    rows = [base] + [summarize(m.fillna(False), fwd, n) for n, m in candidates]
    lines.append("## 1) 日足グリッド（H=10日）")
    lines.append("")
    lines.append(
        f"Baseline: n={base['n']}, mean={base['mean']:.2%}, beat_cost={base['beat_cost_rate']:.1%}"
    )
    lines.append("")
    lines.extend(table_lines([r for r in rows if r["name"] != "ALL_1D"], min_n=20))
    lines.append("")
    # note prior R-001 fail
    lines.append(
        "> 注: `D_near_high_expanded` は HYP-011 として Set B formal **FAIL**。"
        "Discovery 偏り≠検証。同条件の再チューニング禁止。"
    )
    lines.append("")


def run_4h(lines: list[str]) -> None:
    # 12 bars * 4h = 48h forward
    H = 12
    raw = load_csv(DISCOVERY_4H)
    f = add_common_features(raw, h_fwd=H, hh=20)
    fwd = f["fwd_ret"]
    base = summarize(fwd.notna(), fwd, "ALL_4H")
    candidates = [
        ("H4_break_hh_london", f["up_sig"] & f["london"] & f["above_sma50"]),
        ("H4_break_hh_ny_overlap", f["up_sig"] & f["ny_overlap"] & f["above_sma50"]),
        ("H4_break_hh_asia_thin", f["up_sig"] & f["asia_thin"] & f["above_sma50"]),
        ("H4_near_high_expanded_london", f["near_high"] & f["expanded"] & f["london"] & f["above_sma50"]),
        ("H4_compress_then_up_sig", f["compressed"].shift(1).fillna(False) & f["up_sig"] & f["london"]),
        ("H4_half_pb_uptrend_london", f["half_pb"] & f["above_sma50"] & f["sma50_up"] & f["london"]),
        ("H4_up_sig_not_asia", f["up_sig"] & (~f["asia_thin"]) & f["above_sma50"]),
        ("H4_failed_ll_reclaim", (
            f["break_ll"].shift(1).fillna(False)
            & (f["close"] > f["ll"].shift(1))
            & f["above_sma50"]
            & f["london"]
        )),
        ("H4_shallow_pb_expanded", f["shallow_pb"] & f["expanded"] & f["above_sma50"]),
        ("H4_monday_london_break", (f["weekday"] == 0) & f["up_sig"] & f["london"]),
    ]
    rows = [summarize(m.fillna(False), fwd, n) for n, m in candidates]
    lines.append("## 2) 4Hグリッド（H=12本 ≒48時間）")
    lines.append("")
    lines.append(
        f"Baseline: n={base['n']}, mean={base['mean']:.2%}, beat_cost={base['beat_cost_rate']:.1%}"
    )
    lines.append("")
    lines.extend(table_lines(rows, min_n=40))
    lines.append("")

    # Top narratives
    ranked = [r for r in rows if r.get("n", 0) >= 40]
    ranked.sort(key=lambda r: r["mean"], reverse=True)
    lines.append("### 4Hから文章化したい上位（未検証）")
    lines.append("")
    narr = {
        "H4_break_hh_london": (
            "ロンドン時間の4H高値更新は、アジア薄い時間の同形より続きやすい可能性。"
            "薄い時間の初動を見送り、厚い時間の本突破だけを狙う（DEEP D-001/D-007 系）。"
        ),
        "H4_break_hh_ny_overlap": (
            "NY重なりでの高値更新は流動性が乗りやすい。アジア突破の追いかけと区別する。"
        ),
        "H4_break_hh_asia_thin": (
            "アジア突破が弱い／だましが多い対照仮説。撃たないゲートの材料。"
        ),
        "H4_compress_then_up_sig": (
            "4H圧縮後のロンドン突破。日足よりイベント頻度が上がりやすい。"
        ),
        "H4_up_sig_not_asia": (
            "アジア以外の4H上抜け全般。セッション・ゲートの粗い版。"
        ),
        "H4_failed_ll_reclaim": (
            "ロンドンでの下抜け失敗→回復×上昇残存（DEEP D-004 の4H版）。"
        ),
        "H4_near_high_expanded_london": (
            "勢い付き高値圏をロンドンに限定。日足R-001のセッション絞り。"
        ),
        "H4_half_pb_uptrend_london": (
            "上昇中の半値押しをロンドン時間だけ。"
        ),
        "H4_shallow_pb_expanded": (
            "浅い押し＋ボラ拡大。押しの質×勢い。"
        ),
        "H4_monday_london_break": (
            "月曜ロンドンの高値更新。週末ノイズ明けの本方向。"
        ),
    }
    for i, r in enumerate(ranked[:5], 1):
        edge = r["mean"] - base["mean"]
        lines.append(f"#### R4H-00{i} `{r['name']}`")
        lines.append("")
        lines.append(
            f"mean **{r['mean']:.2%}**（全日比 {edge:+.2%}）, n={r['n']}, "
            f"beat_cost={r['beat_cost_rate']:.1%}。"
        )
        lines.append("")
        lines.append(f"**仮説文:** {narr.get(r['name'], 'チャート言葉へ翻訳すること。')}")
        lines.append("")
        lines.append("次: SPOT-R4H 詳細 → 実証② → **Set B のみ** formal eval。")
        lines.append("")


def run_big_move_profile(lines: list[str]) -> None:
    """系統C: 大きく伸びた局面を集め、直前特徴の偏りを見る。"""
    H = 12
    raw = load_csv(DISCOVERY_4H)
    f = add_common_features(raw, h_fwd=H, hh=20)
    fwd = f["fwd_ret"]
    mfe = f["fwd_mfe"]
    # Big long move: top decile of forward return among valid
    valid = fwd.notna()
    thr_ret = float(fwd[valid].quantile(0.90))
    thr_mfe = float(mfe[valid].quantile(0.90))
    big_ret = valid & (fwd >= thr_ret)
    big_mfe = valid & (mfe >= thr_mfe)

    lines.append("## 3) 大きな伸び局面プロファイル（4H・系統C）")
    lines.append("")
    lines.append(
        f"Forward H={H}本。大きな伸び = fwd_ret 上位10%（閾値 {thr_ret:.2%}）"
        f" / MFE 上位10%（閾値 {thr_mfe:.2%}）。"
    )
    lines.append("")
    lines.append(f"大きな伸び(fwd) n={int(big_ret.sum())} / 全日 n={int(valid.sum())}")
    lines.append("")

    feat_cols = [
        ("compressed", "圧縮"),
        ("expanded", "拡大"),
        ("near_high", "高値帯"),
        ("near_low", "安値帯"),
        ("above_sma50", "SMA50上"),
        ("up_sig", "HH更新シグ"),
        ("shallow_pb", "浅い押し"),
        ("london", "ロンドン時間"),
        ("ny_overlap", "NY重なり"),
        ("asia_thin", "アジア薄い"),
        ("bull", "陽線"),
    ]

    def profile(mask: pd.Series) -> list[tuple[str, float, float, float]]:
        bits = []
        for col, label in feat_cols:
            rate_all = float(f.loc[valid, col].fillna(False).mean())
            rate_big = float(f.loc[mask, col].fillna(False).mean()) if mask.any() else float("nan")
            bits.append((label, rate_all, rate_big, rate_big - rate_all))
        return sorted(bits, key=lambda x: -x[3])

    lines.append("### 3a — fwd_ret 上位10%の直前偏り")
    lines.append("")
    lines.append("| 特徴 | 全日 | 伸び局面 | 差 |")
    lines.append("|------|------|----------|----|")
    for label, a, b, d in profile(big_ret):
        lines.append(f"| {label} | {a:.1%} | {b:.1%} | {d:+.1%} |")
    lines.append("")

    lines.append("### 3b — MFE 上位10%の直前偏り")
    lines.append("")
    lines.append("| 特徴 | 全日 | 伸び局面 | 差 |")
    lines.append("|------|------|----------|----|")
    for label, a, b, d in profile(big_mfe):
        lines.append(f"| {label} | {a:.1%} | {b:.1%} | {d:+.1%} |")
    lines.append("")

    # Combine top positive biases into a candidate spot sentence
    top = profile(big_ret)[:3]
    labels = " × ".join(t[0] for t in top if t[3] > 0)
    lines.append("### 系統Cから①へ（文章・未検証）")
    lines.append("")
    lines.append(
        f"**R-BM-001:** 4Hでその後大きく伸びた局面の直前は、全日より "
        f"**{labels}** が多かった。"
        "→『大きな伸びの入口』を、これらの複合として定義し、"
        "イベント頻度が日足より高い仮説にする。"
    )
    lines.append("")
    lines.append(
        "**攻め方の仮:** 伸びた結果を追うのではなく、偏りが乗った条件が揃った時点で入る。"
        "アジア薄いは伸び局面で少ない／負の偏りなら撃たないゲート候補。"
    )
    lines.append("")


def main() -> None:
    lines = [
        "# データ逆算ディスカバリ結果（Discovery のみ）",
        "",
        "**検証ではない。** Holdout / formal eval の合否は出していない。",
        "",
        f"- Discovery 1D: `{DISCOVERY_1D.name}`",
        f"- Discovery 4H: `{DISCOVERY_4H.name}`",
        f"- Holdout（未使用）: {HOLDOUT_NOTE}",
        "- 手法: [../craft/REVERSE_DISCOVERY.md](../craft/REVERSE_DISCOVERY.md)",
        "- 費用proxy: 0.20% round-trip",
        "",
    ]
    run_1d(lines)
    run_4h(lines)
    run_big_move_profile(lines)
    lines.append("---")
    lines.append("")
    lines.append("*生成: `scripts/reverse_discover_spots.py`*")
    text = "\n".join(lines) + "\n"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
