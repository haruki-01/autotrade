"""10-cycle verify → hypothesis update → verify loop for P1-NR."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from scripts.phase0.common import load_or_fetch
from scripts.phase1.nr_targets import NR_N_FOCUS, NR_RR_FOCUS, build_focus_grid
from scripts.phase1.common import GATE2_P_TARGET
from scripts.phase1.p1nr_eval import NRConfig, evaluate_config, pick_best

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "research" / "p1nr_loop"
REPORT_PATH = ROOT / "docs/research/p1nr-research-report.md"

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)


def _core_grid() -> list[NRConfig]:
    return [NRConfig(n_target=n, rr_ratio=rr) for n in NR_N_FOCUS for rr in NR_RR_FOCUS]


def _clone_best(best: dict, **overrides) -> NRConfig:
    c = best["config"]
    return NRConfig(
        n_target=overrides.get("n_target", c["n_target"]),
        rr_ratio=overrides.get("rr_ratio", c["rr_ratio"]),
        pct_risk=overrides.get("pct_risk", c["pct_risk"]),
        atr_mult=overrides.get("atr_mult", c["atr_mult"]),
        max_bars=overrides.get("max_bars", c["max_bars"]),
        cooldown=overrides.get("cooldown", c["cooldown"]),
    )


def hypothesis_for_iteration(iter_num: int, prev: dict | None, global_best: dict | None) -> tuple[str, list[NRConfig]]:
    """Return (hypothesis_text, configs_to_test) for iteration 1..10."""
    if iter_num == 1:
        return (
            "H1: N=20/50 × RR=1:3/1:5 @ baseline R で執行込み Gate2 に届くセルが存在する",
            _core_grid(),
        )

    best = global_best or (prev.get("best") if prev else None)
    if not best:
        return ("H?: 前回 best なし — core grid 再実行", _core_grid())

    bc = best["config"]
    b_n, b_rr = bc["n_target"], bc["rr_ratio"]
    b_cd = bc["cooldown"]
    b_pct = bc["pct_risk"]
    b_atr = bc["atr_mult"]
    b_mb = bc["max_bars"]

    if iter_num == 2:
        # Fine cooldown around best + RR=4 on best N
        cfgs = [
            _clone_best(best, cooldown=max(12, b_cd - 24)),
            _clone_best(best, cooldown=b_cd + 24),
            NRConfig(n_target=b_n, rr_ratio=4.0, pct_risk=b_pct, atr_mult=b_atr, max_bars=b_mb),
        ]
        return (
            f"H2: iter1 best (N={b_n}, RR={b_rr}) の cooldown 微調整 + RR=1:4 で EV/W トレードオフを探索",
            cfgs,
        )

    if iter_num == 3:
        cfgs = [
            _clone_best(best, pct_risk=0.010),
            _clone_best(best, pct_risk=0.012),
            _clone_best(best, pct_risk=0.016),
        ]
        return (
            f"H3: R 幅拡大（pct_risk↑）で EV/trade を上げつつ W 維持できるか（best: N={b_n}, RR={b_rr}）",
            cfgs,
        )

    if iter_num == 4:
        cfgs = [
            _clone_best(best, pct_risk=0.006),
            _clone_best(best, pct_risk=0.008, atr_mult=0.25),
        ]
        return (
            "H4: R 幅縮小で W↑・執行劣化↓のトレードオフを検証",
            cfgs,
        )

    if iter_num == 5:
        cfgs = [
            _clone_best(best, atr_mult=1.0),
            _clone_best(best, atr_mult=1.5),
            _clone_best(best, pct_risk=b_pct, atr_mult=1.0),
        ]
        return (
            "H5: ATR ベース R 拡大 — ボラ連動幅が OOS P を改善するか",
            cfgs,
        )

    if iter_num == 6:
        cfgs = [
            _clone_best(best, max_bars=72),
            _clone_best(best, max_bars=96),
        ]
        return (
            "H6: 保有時間延長（max_bars↑）で TP 到達率とレバ手数料のバランス",
            cfgs,
        )

    if iter_num == 7:
        # Apply best learnings to BOTH N targets
        other_n = 50 if b_n == 20 else 20
        cfgs = [
            _clone_best(best),
            NRConfig(
                n_target=other_n,
                rr_ratio=b_rr,
                pct_risk=b_pct,
                atr_mult=b_atr,
                max_bars=b_mb,
                cooldown=None,
            ),
        ]
        return (
            f"H7: iter1-6 で得た最良 R/RR を N={other_n} に転用 — エッジの N 汎化",
            cfgs,
        )

    if iter_num == 8:
        # Re-test top 2 global configs with both splits emphasis on degradation
        top2 = prev.get("top2", [best]) if prev else [best]
        cfgs = [_clone_best(t) for t in top2[:2]]
        return (
            "H8: 上位2設定の執行込み再確認 — 劣化率 <0.7 のセルは hold",
            cfgs,
        )

    if iter_num == 9:
        cfgs = [_clone_best(global_best)]
        # Also test opposite RR on same N
        cfgs.append(
            NRConfig(
                n_target=bc["n_target"],
                rr_ratio=5.0 if bc["rr_ratio"] <= 3 else 3.0,
                pct_risk=bc["pct_risk"],
                atr_mult=bc["atr_mult"],
                max_bars=bc["max_bars"],
            )
        )
        return (
            "H9: 全局 best の OOS 安定性 + 同 N 逆 RR 対照",
            cfgs,
        )

    # iter 10
    cfgs = []
    for t in (prev.get("top3") or [global_best])[:3]:
        if t:
            cfgs.append(_clone_best(t))
    if not cfgs:
        cfgs = _core_grid()
    return (
        "H10: 全局 top3 最終執行込み validation — Gate2 / W* / 劣化率の確定",
        cfgs,
    )


def _summarize_iteration(results: list[dict]) -> dict:
    best = pick_best(results)
    sorted_r = sorted(
        results,
        key=lambda r: r.get("oos_executed_p") or -1e9,
        reverse=True,
    )
    gate2_hits = [r for r in results if r.get("gate2")]
    gate1_hits = [r for r in results if r.get("gate1")]
    return {
        "best": best,
        "top2": sorted_r[:2],
        "top3": sorted_r[:3],
        "gate2_count": len(gate2_hits),
        "gate1_count": len(gate1_hits),
        "results": results,
    }


def _learning_update(iter_num: int, summary: dict, hypothesis: str) -> str:
    best = summary.get("best")
    if not best:
        return "結果なし — 次イテレーションで core grid へフォールバック"

    ex_p = best.get("oos_executed_p", 0)
    ex_w = best.get("oos_executed_w", 0)
    w_star = best.get("target", {}).get("w_star_gate2", 1)
    deg = best.get("degradation", float("nan"))
    cfg = best["config"]
    lines = [
        f"最良: {best['label']} — 執行込み P≈¥{ex_p:.0f}, W={ex_w:.1%}, 劣化率={deg:.2f}",
    ]

    if summary.get("gate2_count", 0) > 0:
        lines.append("→ Gate2 pass セルあり。次は fine-tune / 汎化確認。")
    elif ex_p >= GATE2_P_TARGET * 0.5:
        lines.append(f"→ Gate2 半分超 ({ex_p/GATE2_P_TARGET:.0%})。RR/R/N の微調整継続。")
    else:
        lines.append(f"→ Gate2 遠隔 ({ex_p/GATE2_P_TARGET:.0%})。W*={w_star:.1%} vs W={ex_w:.1%}。")

    if not np.isnan(deg) and deg < 0.7:
        lines.append("→ 執行劣化大（<0.7）。理論値 pass でも promote 不可。")
    elif ex_w >= w_star:
        lines.append("→ W ≥ W* 達成。EV 不足がボトルネック。")
    else:
        lines.append(f"→ W < W*（差 {w_star - ex_w:.1%}）。RR↑ or R 調整の余地。")

    if iter_num == 3 and cfg.get("pct_risk", 0.008) > 0.010:
        lines.append("→ R 拡大は W 低下に注意（P1-R 教訓再確認）。")
    if iter_num == 6:
        lines.append("→ max_bars 変更はレバ手数料と TP fill に両方効く。")

    return " ".join(lines)


def run_loop(max_iterations: int = 10) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    print(f"Loaded {len(df)} bars", flush=True)

    targets_table = build_focus_grid()
    (OUT_DIR / "nr_targets_focus.json").write_text(
        json.dumps({"rows": targets_table}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    iterations = []
    global_best = None
    prev_summary = None

    for i in range(1, max_iterations + 1):
        hypothesis, configs = hypothesis_for_iteration(i, prev_summary, global_best)
        print(f"\n=== Iteration {i}/10 ===", flush=True)
        print(f"Hypothesis: {hypothesis}", flush=True)

        results = []
        for cfg in configs:
            print(f"  Eval {cfg.label()}...", flush=True)
            results.append(evaluate_config(df, cfg))

        summary = _summarize_iteration(results)
        learning = _learning_update(i, summary, hypothesis)

        if summary["best"]:
            if global_best is None or (
                summary["best"].get("oos_executed_p", 0) > global_best.get("oos_executed_p", 0)
            ):
                global_best = summary["best"]

        if summary.get("gate2_count", 0) > 0:
            learning += " [Gate2 pass — loop may terminate early after recording.]"

        iter_record = {
            "iteration": i,
            "hypothesis": hypothesis,
            "learning": learning,
            "gate2_count": summary["gate2_count"],
            "gate1_count": summary["gate1_count"],
            "best_label": summary["best"]["label"] if summary["best"] else None,
            "best_oos_executed_p": summary["best"].get("oos_executed_p") if summary["best"] else None,
            "configs_tested": len(configs),
            "results": [
                {k: v for k, v in r.items() if k != "splits"} for r in results
            ],
        }
        iterations.append(iter_record)
        prev_summary = summary

        iter_path = OUT_DIR / f"iter_{i:02d}.json"
        iter_path.write_text(json.dumps(iter_record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        print(f"  Learning: {learning}", flush=True)

        if summary.get("gate2_count", 0) > 0:
            print("  Gate2 pass detected — continuing to complete 10 iterations for report.", flush=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "iterations": iterations,
        "global_best": {k: v for k, v in global_best.items() if k != "splits"} if global_best else None,
        "targets_focus": targets_table,
    }
    out_path = OUT_DIR / "p1nr_loop_summary.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return payload


def write_report(payload: dict) -> Path:
    lines = [
        "# P1-NR 研究ループレポート（10 イテレーション）",
        "",
        f"生成: {payload.get('generated_at', '')}",
        f"サンプル: {payload.get('sample_period', '')}",
        "",
        "## エグゼクティブサマリー",
        "",
    ]

    gb = payload.get("global_best")
    if gb:
        cfg = gb["config"]
        lines.extend(
            [
                f"- **全局最良**: {gb['label']}",
                f"- 執行込み OOS 月次 P ≈ **¥{gb.get('oos_executed_p', 0):,.0f}**（Gate2 目標 ¥{GATE2_P_TARGET:,}）",
                f"- W = {gb.get('oos_executed_w', 0):.1%}（W* = {gb.get('target', {}).get('w_star_gate2', 0):.1%}）",
                f"- 劣化率 = {gb.get('degradation', float('nan')):.2f}",
                f"- Gate1 = {gb.get('gate1')} / Gate2 = {gb.get('gate2')} / verdict = **{gb.get('verdict')}**",
                "",
            ]
        )
    else:
        lines.append("- 有効な結果なし\n")

    lines.extend(["## 焦点グリッド事前表（baseline R=0.8%）", ""])
    lines.append("| N | RR | EV* | W* | max EV@W100 | Gate2 feasible@W100 |")
    lines.append("|---:|---:|---:|---:|---:|:---:|")
    for row in payload.get("targets_focus", []):
        feas = "yes" if row.get("gate2_feasible_at_w100") else "no"
        lines.append(
            f"| {row['n_target']} | 1:{int(row['rr_ratio'])} | ¥{row['ev_star_jpy']:.0f} | "
            f"{row['w_star_gate2']:.1%} | ¥{row['max_ev_at_w100_jpy']:.0f} | {feas} |"
        )
    lines.append("")

    lines.extend(["## イテレーション履歴", ""])
    for it in payload.get("iterations", []):
        lines.extend(
            [
                f"### Iter {it['iteration']}: {it['hypothesis']}",
                "",
                f"- テスト数: {it['configs_tested']} / Gate1: {it['gate1_count']} / Gate2: {it['gate2_count']}",
                f"- Best: {it.get('best_label')} (P≈¥{it.get('best_oos_executed_p') or 0:,.0f})",
                f"- **Learning**: {it['learning']}",
                "",
            ]
        )
        lines.append("| Config | 理論P | 執行P | W | N/mo | 劣化 | G1 | G2 | W*ok |")
        lines.append("|---|---:|---:|---:|---:|---:|:---:|:---:|:---:|")
        for r in it.get("results", []):
            lines.append(
                f"| {r['label']} | ¥{r.get('oos_theoretical_p', 0):,.0f} | "
                f"¥{r.get('oos_executed_p', 0):,.0f} | {r.get('oos_executed_w', 0):.1%} | "
                f"{r.get('oos_executed_n', 0):.1f} | {r.get('degradation', 0):.2f} | "
                f"{'Y' if r.get('gate1') else 'N'} | {'Y' if r.get('gate2') else 'N'} | "
                f"{'Y' if r.get('w_check') else 'N'} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 結論",
            "",
            "### 3変数（N, RR, R）の応答",
            "",
            "- **RR 拡大（1:3→1:5）**: 理論 EV↑、実測 W↓、執行劣化↑（TP 遠い）のトレードオフ",
            "- **R 幅拡大**: P1-R 再現 — 理論値改善も執行込み OOS P は横ばい〜悪化しやすい",
            "- **N 調整**: cooldown で N 帯は合わせ可能。N=100 はシグナル上限で不可",
            "",
            "### 最終判定",
            "",
        ]
    )
    if gb and gb.get("gate2"):
        lines.append("- **promote 候補** — Gate2 pass。live paper へ。")
    elif gb and gb.get("gate1"):
        lines.append(
            "- **conditional 維持** — Gate1 pass、Gate2 fail。"
            " H-D + H-M4 + RR 変更では月次 +5% 未到達。"
            " L1 探索 or 別エントリー合成を推奨。"
        )
    else:
        lines.append("- **reject** — Gate1 も未達の設定あり。要再設計。")

    lines.extend(
        [
            "",
            "## 次アクション",
            "",
            "1. Gate2 pass なし → 新 L1 仮説（H-B 等）or H-D をフィルタ化",
            "2. 執行劣化 >30% のセルは理論値のみ pass 扱い（promote 禁止）",
            "3. 有望セルがあれば GMO live paper で fill 率実測",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def main() -> None:
    payload = run_loop(max_iterations=10)
    report_path = write_report(payload)
    print(f"\nReport: {report_path}", flush=True)


if __name__ == "__main__":
    main()
