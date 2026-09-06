"""10-cycle P3-B-NR: H-F3 N-band expansion research loop."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from scripts.phase0.common import load_or_fetch
from scripts.phase1.p3bnr_eval import HF3NRConfig, evaluate_config, pick_best, pick_best_gate1
from scripts.research.preflight import batch_metadata

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "research" / "p3bnr_loop"
REPORT_PATH = ROOT / "docs/research/p3bnr-research-report.md"

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)

BASELINE = HF3NRConfig(cooldown=12, range_quantile=0.20, atr_touch_mult=0.10)


def _clone_cfg(cfg: HF3NRConfig, **overrides) -> HF3NRConfig:
    d = asdict(cfg)
    d.update(overrides)
    return HF3NRConfig(**d)


def _clone_best(best: dict, **overrides) -> HF3NRConfig:
    return HF3NRConfig(**{**best["config"], **overrides})


def hypothesis_for_iteration(
    iter_num: int,
    prev: dict | None,
    global_best: dict | None,
) -> tuple[str, list[HF3NRConfig], bool]:
    """Return (hypothesis, configs, use_auto_cooldown)."""
    if iter_num == 1:
        cfgs = [_clone_cfg(BASELINE, cooldown=cd) for cd in (4, 6, 8, 12, 24)]
        return (
            "H1: cooldown 短縮（4–24）で N 帯 40–60 に近づけつつ OOS 執行 EV>0 を探す",
            cfgs,
            False,
        )

    best = global_best or (prev.get("best") if prev else None)
    if not best:
        cfgs = [_clone_cfg(BASELINE, cooldown=cd) for cd in (4, 8, 12)]
        return ("H?: fallback cooldown grid", cfgs, False)

    bc = best["config"]

    if iter_num == 2:
        cfgs = [
            _clone_best(best, range_quantile=0.25),
            _clone_best(best, range_quantile=0.30),
            _clone_best(best, range_quantile=0.35),
        ]
        return (
            f"H2: range_quantile 緩和（イベント増）— best cd={bc['cooldown']}",
            cfgs,
            False,
        )

    if iter_num == 3:
        cfgs = [
            _clone_best(best, atr_touch_mult=0.12),
            _clone_best(best, atr_touch_mult=0.15),
            _clone_best(best, atr_touch_mult=0.20),
        ]
        return (
            "H3: edge touch 幅拡大（atr_touch↑）で N↑・edge 維持できるか",
            cfgs,
            False,
        )

    if iter_num == 4:
        cfgs = [
            _clone_best(best, rr_ratio=2.0),
            _clone_best(best, rr_ratio=3.0),
        ]
        return ("H4: RR 1:2 vs 1:3 — EV/N トレードオフ", cfgs, False)

    if iter_num == 5:
        cfgs = [
            _clone_best(best, pct_risk=0.008),
            _clone_best(best, pct_risk=0.012),
        ]
        return ("H5: R 幅（pct_risk）調整", cfgs, False)

    if iter_num == 6:
        cfgs = [_clone_best(best)]
        return (
            f"H6: auto cooldown で N={bc.get('n_target', 50)} 最適化",
            cfgs,
            True,
        )

    if iter_num == 7:
        cfgs = [
            _clone_best(best, max_bars=36),
            _clone_best(best, max_bars=48),
        ]
        return ("H7: max_bars 延長 — TP 到達とレバ手数料", cfgs, False)

    if iter_num == 8:
        top2 = prev.get("top2", [best]) if prev else [best]
        cfgs = [_clone_best(t) for t in top2[:2]]
        return ("H8: 上位2設定の執行込み再確認", cfgs, True)

    if iter_num == 9:
        cfgs = [
            _clone_best(best, n_target=40),
            _clone_best(best, n_target=50),
            _clone_best(best, n_target=60),
        ]
        return ("H9: N ターゲット 40/50/60 で auto cooldown 比較", cfgs, True)

    top3 = (prev.get("top3") or [global_best])[:3] if prev else [global_best]
    cfgs = [_clone_best(t) for t in top3 if t]
    return ("H10: 全局 top3 最終 validation", cfgs, True)


def _summarize_iteration(results: list[dict]) -> dict:
    best = pick_best_gate1(results) or pick_best(results)
    sorted_r = sorted(results, key=lambda r: r.get("oos_executed_p") or -1e9, reverse=True)
    return {
        "best": best,
        "top2": sorted_r[:2],
        "top3": sorted_r[:3],
        "gate2_count": sum(1 for r in results if r.get("gate2")),
        "gate1_count": sum(1 for r in results if r.get("gate1")),
        "results": results,
    }


def _learning_update(iter_num: int, summary: dict) -> str:
    best = summary.get("best")
    if not best:
        return "結果なし"
    ex_p = best.get("oos_executed_p", 0)
    ex_n = best.get("oos_executed_n", 0)
    ex_w = best.get("oos_executed_w", 0)
    ex_ev = best.get("oos_executed_ev", 0)
    deg = best.get("degradation", float("nan"))
    g1 = best.get("gate1")
    lines = [
        f"最良: {best['label']} — P≈¥{ex_p:.0f}, N={ex_n:.1f}/mo, W={ex_w:.1%}, EV=¥{ex_ev:.1f}",
    ]
    if summary.get("gate2_count"):
        lines.append("→ Gate2 pass。")
    elif g1:
        lines.append("→ Gate1 pass。Gate2 未到達。")
    elif ex_ev > 0:
        lines.append(f"→ EV>0 だが N 帯外（N={ex_n:.1f}）。N 拡大継続。")
    else:
        lines.append("→ EV≤0。検出緩和 or 別 L1。")
    if not np.isnan(deg):
        lines.append(f"劣化率={deg:.2f}。")
    return " ".join(lines)


def run_loop(max_iterations: int = 10) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    print(f"Loaded {len(df)} bars", flush=True)

    iterations = []
    global_best = None
    prev_summary = None
    stale_gate1 = 0

    for i in range(1, max_iterations + 1):
        hypothesis, configs, auto_cd = hypothesis_for_iteration(i, prev_summary, global_best)
        print(f"\n=== Iteration {i}/{max_iterations} ===", flush=True)
        print(f"Hypothesis: {hypothesis}", flush=True)

        results = []
        for cfg in configs:
            print(f"  Eval {cfg.label()}...", flush=True)
            results.append(evaluate_config(df, cfg, auto_cooldown=auto_cd))

        summary = _summarize_iteration(results)
        learning = _learning_update(i, summary)

        if summary["best"]:
            cand = summary["best"]
            if global_best is None or (cand.get("oos_executed_p", 0) > global_best.get("oos_executed_p", 0)):
                global_best = cand

        prev_g1 = prev_summary.get("gate1_count", 0) if prev_summary else 0
        if summary.get("gate1_count", 0) <= prev_g1 and i > 3:
            stale_gate1 += 1
        else:
            stale_gate1 = 0

        iter_record = {
            "iteration": i,
            "hypothesis": hypothesis,
            "learning": learning,
            "auto_cooldown": auto_cd,
            "gate2_count": summary["gate2_count"],
            "gate1_count": summary["gate1_count"],
            "best_label": summary["best"]["label"] if summary["best"] else None,
            "best_oos_executed_p": summary["best"].get("oos_executed_p") if summary["best"] else None,
            "best_oos_executed_n": summary["best"].get("oos_executed_n") if summary["best"] else None,
            "configs_tested": len(configs),
            "results": [{k: v for k, v in r.items() if k != "splits"} for r in results],
        }
        iterations.append(iter_record)
        prev_summary = summary

        path = OUT_DIR / f"iter_{i:02d}.json"
        path.write_text(json.dumps(iter_record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        print(f"  Learning: {learning}", flush=True)

        if stale_gate1 >= 3 and i >= 6:
            print("  Stop: 3 iter without Gate1 improvement.", flush=True)
            break

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "iterations": iterations,
        "global_best": {k: v for k, v in global_best.items() if k != "splits"} if global_best else None,
        **batch_metadata(),
    }
    out = OUT_DIR / "p3bnr_loop_summary.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return payload


def write_report(payload: dict) -> Path:
    lines = [
        "# P3-B-NR 研究ループレポート（H-F3 N 拡大）",
        "",
        f"生成: {payload.get('generated_at', '')}",
        f"サンプル: {payload.get('sample_period', '')}",
        "",
        "## エグゼクティブサマリー",
        "",
    ]
    gb = payload.get("global_best")
    if gb:
        lines.extend(
            [
                f"- **全局最良**: {gb['label']}",
                f"- 執行込み OOS P ≈ **¥{gb.get('oos_executed_p', 0):,.0f}**（Gate2 目標 ¥2,500）",
                f"- N = {gb.get('oos_executed_n', 0):.1f}/月（帯 40–60）",
                f"- W = {gb.get('oos_executed_w', 0):.1%}",
                f"- Gate1 = {gb.get('gate1')} / Gate2 = {gb.get('gate2')}",
                "",
            ]
        )
    else:
        lines.append("- 有効な結果なし\n")

    lines.extend(["## イテレーション履歴", ""])
    for it in payload.get("iterations", []):
        lines.extend(
            [
                f"### Iter {it['iteration']}: {it['hypothesis']}",
                "",
                f"- テスト数: {it['configs_tested']} / Gate1: {it['gate1_count']} / Gate2: {it['gate2_count']}",
                f"- Best: {it.get('best_label')} (P≈¥{it.get('best_oos_executed_p') or 0:,.0f}, N={it.get('best_oos_executed_n') or 0:.1f})",
                f"- **Learning**: {it['learning']}",
                "",
                "| Config | 執行P | W | N/mo | 劣化 | G1 | G2 |",
                "|---|---:|---:|---:|---:|:---:|:---:|",
            ]
        )
        for r in it.get("results", []):
            lines.append(
                f"| {r['label']} | ¥{r.get('oos_executed_p', 0):,.0f} | "
                f"{r.get('oos_executed_w', 0):.1%} | {r.get('oos_executed_n', 0):.1f} | "
                f"{r.get('degradation', 0):.2f} | {'Y' if r.get('gate1') else 'N'} | "
                f"{'Y' if r.get('gate2') else 'N'} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 結論",
            "",
        ]
    )
    if gb and gb.get("gate2"):
        lines.append("- **promote** — Gate2 pass。")
    elif gb and gb.get("gate1"):
        lines.append("- **conditional** — Gate1 pass。P3-C（H-D filter）へ。")
    elif gb and (gb.get("oos_executed_ev") or 0) > 0:
        lines.append("- **conditional（N 不足）** — EV 正だが N 帯未達。検出定義見直し or 別 L1。")
    else:
        lines.append("- **reject** — H-F3 N 拡大では Gate1 未到達。")

    lines.extend(
        [
            "",
            "## 次アクション",
            "",
            "1. Gate1 pass → P3-C（H-D filter + H-F3）",
            "2. Gate1 fail → H-F3 棄却、H-D hold 継続",
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
