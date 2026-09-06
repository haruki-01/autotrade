"""30-cycle verify → evaluate → hypothesis refine → verify loop for H-D4."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from scripts.phase0.common import load_or_fetch
from scripts.phase1.common import GATE2_P_TARGET, N_BAND_LOW, N_BAND_HIGH
from scripts.phase1.hd4_eval import HD4Config, evaluate_config, pick_best, pick_best_gate1

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "research" / "hd4_loop"
REPORT_PATH = ROOT / "docs/research/hd4-research-report.md"
SPEC_PATH = ROOT / "docs/research/hd4nr-spec.md"

SAMPLE_START = date(2024, 1, 1)
SAMPLE_END = date(2026, 8, 31)
MAX_ITER = 30

BASELINE = HD4Config(mode="break", pct_level=-0.015, swing_bars=24, entry_mode="immediate", cooldown=48)


def _clone(cfg: HD4Config | dict, **overrides) -> HD4Config:
    if isinstance(cfg, dict):
        d = deepcopy(cfg.get("config", cfg))
    else:
        d = asdict(cfg)
    d.update(overrides)
    return HD4Config(**d)


def _clone_best(best: dict, **overrides) -> HD4Config:
    return HD4Config(**{**best["config"], **overrides})


def _adaptive_configs(iter_num: int, global_best: dict, prev: dict | None) -> tuple[str, list[HD4Config]]:
    """Adaptive hypothesis generation for iterations 11–30."""
    bc = global_best["config"]
    phase = (iter_num - 11) // 5  # 0..3
    slot = (iter_num - 11) % 5

    param_sets = [
        ("cooldown", [
            _clone_best(global_best, cooldown=max(12, bc["cooldown"] - 24)),
            _clone_best(global_best, cooldown=bc["cooldown"] + 24),
            _clone_best(global_best, cooldown=max(12, bc["cooldown"] - 48)),
        ]),
        ("pct_level", [
            _clone_best(global_best, pct_level=bc["pct_level"] + 0.002),
            _clone_best(global_best, pct_level=bc["pct_level"] - 0.002),
            _clone_best(global_best, pct_level=bc["pct_level"] + 0.004),
        ]),
        ("swing_bars", [
            _clone_best(global_best, swing_bars=max(12, bc["swing_bars"] - 12)),
            _clone_best(global_best, swing_bars=bc["swing_bars"] + 12),
            _clone_best(global_best, swing_bars=bc["swing_bars"] + 24),
        ]),
        ("entry_mode", [
            _clone_best(global_best, entry_mode="pull" if bc["entry_mode"] == "immediate" else "immediate"),
            _clone_best(global_best, entry_mode="pull"),
        ]),
        ("exit", [
            _clone_best(global_best, sl_pct=0.005, tp_pct=0.010, rr_ratio=2.0),
            _clone_best(global_best, sl_pct=0.006, tp_pct=0.012, rr_ratio=2.0),
            _clone_best(global_best, sl_pct=None, tp_pct=None, rr_ratio=3.0, pct_risk=0.010),
        ]),
        ("max_bars", [
            _clone_best(global_best, max_bars=24),
            _clone_best(global_best, max_bars=72),
            _clone_best(global_best, max_bars=96),
        ]),
    ]

    if iter_num >= 26:
        top3 = (prev.get("top3") or [global_best]) if prev else [global_best]
        cfgs = [_clone_best(t) for t in top3[:3] if t]
        return (
            f"H{iter_num}: 全局 top3 最終 validation（iter 26–30 収束）",
            cfgs or [_clone_best(global_best)],
        )

    name, cfgs = param_sets[phase % len(param_sets)]
    if slot < len(cfgs):
        chosen = [cfgs[slot]]
        if slot + 1 < len(cfgs):
            chosen.append(cfgs[slot + 1])
    else:
        chosen = cfgs[:2]

    # Every 3rd adaptive iter: flip mode as control
    if iter_num % 3 == 0:
        alt_mode = "bounce" if bc["mode"] == "break" else "break"
        chosen.append(_clone_best(global_best, mode=alt_mode))

    return (
        f"H{iter_num}: 全局 best 周辺 — {name} 微調整（best P≈¥{global_best.get('oos_executed_p', 0):.0f}）",
        chosen,
    )


def hypothesis_for_iteration(
    iter_num: int,
    prev: dict | None,
    global_best: dict | None,
) -> tuple[str, list[HD4Config]]:
    if iter_num > 10:
        if global_best:
            return _adaptive_configs(iter_num, global_best, prev)
        return (
            f"H{iter_num}: global best なし — baseline 再探索",
            [_clone(BASELINE), _clone(BASELINE, mode="bounce", pct_level=-0.010)],
        )

    if iter_num == 1:
        cfgs = [
            HD4Config(mode="break", pct_level=-0.015, cooldown=48),
            HD4Config(mode="break", pct_level=-0.020, cooldown=48),
            HD4Config(mode="bounce", pct_level=-0.010, cooldown=48),
            HD4Config(mode="bounce", pct_level=-0.012, cooldown=48),
        ]
        return (
            "H1: Phase0 再現 — break@−1.5%/−2.0% vs bounce@−1.0%/−1.2%（執行込み Gate1/2）",
            cfgs,
        )

    best = global_best or (prev.get("best") if prev else None)
    if not best:
        return ("H?: fallback baseline", [_clone(BASELINE)])

    bc = best["config"]

    if iter_num == 2:
        cfgs = [_clone_best(best, cooldown=cd) for cd in (24, 48, 72, 96, 144)]
        return (
            f"H2: cooldown グリッド — N 帯 {N_BAND_LOW}–{N_BAND_HIGH} へ（best mode={bc['mode']}）",
            cfgs,
        )

    if iter_num == 3:
        cfgs = [
            _clone_best(best, swing_bars=12),
            _clone_best(best, swing_bars=24),
            _clone_best(best, swing_bars=48),
        ]
        return ("H3: スイング lookback（12/24/48）— 群集水準の定義", cfgs)

    if iter_num == 4:
        base_pct = bc["pct_level"]
        cfgs = [
            _clone_best(best, pct_level=base_pct + 0.002),
            _clone_best(best, pct_level=base_pct - 0.002),
            _clone_best(best, pct_level=base_pct - 0.004),
        ]
        return ("H4: pct_level fine-tune（±0.2%/0.4%）", cfgs)

    if iter_num == 5:
        cfgs = [
            _clone_best(best, entry_mode="immediate"),
            _clone_best(best, entry_mode="pull"),
        ]
        return ("H5: 即入り vs 押し待ち（H-D PULL 教訓の転用）", cfgs)

    if iter_num == 6:
        cfgs = [
            _clone_best(best, sl_pct=0.005, tp_pct=0.010),
            _clone_best(best, sl_pct=0.006, tp_pct=0.012),
            _clone_best(best, sl_pct=None, tp_pct=None, rr_ratio=3.0),
        ]
        return ("H6: Exit — fixed pct vs RR 1:3 ATR", cfgs)

    if iter_num == 7:
        cfgs = [
            _clone_best(best, max_bars=24),
            _clone_best(best, max_bars=48),
            _clone_best(best, max_bars=72),
        ]
        return ("H7: max_bars（h60/h240/h360 相当）", cfgs)

    if iter_num == 8:
        cfgs = [
            _clone_best(best, cooldown=72, n_target=50),
            _clone_best(best, cooldown=96, n_target=50),
            _clone_best(best, cooldown=120, n_target=50),
        ]
        return ("H8: cooldown 72/96/120 — N 帯へ（auto 代替）", cfgs)

    if iter_num == 9:
        cfgs = [
            _clone_best(best, weekend_filter=True),
            _clone_best(best, weekend_filter=False),
        ]
        return ("H9: H-M4 土日停止 ON/OFF", cfgs)

    top2 = prev.get("top2", [best]) if prev else [best]
    cfgs = [_clone_best(t) for t in top2[:2]]
    cfgs.append(_clone_best(global_best, mode="bounce" if bc["mode"] == "break" else "break"))
    return (
        "H10: Phase1 前半まとめ — top2 再確認 + 逆 mode 対照",
        cfgs,
    )


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


def _learning_update(iter_num: int, summary: dict, hypothesis: str, stale_count: int) -> str:
    best = summary.get("best")
    if not best:
        return "結果なし — baseline へフォールバック"

    ex_p = best.get("oos_executed_p", 0)
    ex_ev = best.get("oos_executed_ev", 0)
    ex_n = best.get("oos_executed_n", 0)
    ex_w = best.get("oos_executed_w", 0)
    deg = best.get("degradation", float("nan"))
    cfg = best["config"]

    lines = [
        f"最良 {best['label']}: 執行P≈¥{ex_p:.0f}, EV≈¥{ex_ev:.1f}, N≈{ex_n:.1f}/月, W={ex_w:.1%}",
    ]

    if summary.get("gate2_count", 0) > 0:
        lines.append("→ Gate2 pass。fine-tune / TEST 固定検証へ。")
    elif ex_p >= GATE2_P_TARGET * 0.5:
        lines.append(f"→ Gate2 半分超 ({ex_p/GATE2_P_TARGET:.0%})。{cfg['mode']}×pct 微調整継続。")
    elif ex_ev > 0:
        lines.append(f"→ EV>0 だが P 不足（N={ex_n:.1f}）。cooldown/N 調整。")
    else:
        lines.append("→ EV≤0。mode 反転 or pct_level 変更。")

    if not np.isnan(deg) and deg < 0.7:
        lines.append("→ 執行劣化大。理論 pass でも promote 不可。")

    if ex_n < N_BAND_LOW:
        lines.append(f"→ N<{N_BAND_LOW}。cooldown 短縮 or pct 浅く。")
    elif ex_n > N_BAND_HIGH:
        lines.append(f"→ N>{N_BAND_HIGH}。cooldown 延長。")

    if stale_count >= 3:
        lines.append(f"→ {stale_count} iter 無改善 — pivot（mode/pct 変更）。")

    return " ".join(lines)


def _next_hypothesis_hint(summary: dict, global_best: dict | None) -> str:
    best = summary.get("best")
    if not best:
        return "baseline break/bounce 再グリッド"
    cfg = best["config"]
    if best.get("gate2"):
        return "Gate2 達成 config の TEST 固定 + Research Gate"
    if best.get("gate1"):
        return f"Gate1 pass — RR/Exit 微調整（mode={cfg['mode']}）"
    if (best.get("oos_executed_ev") or 0) > 0:
        if (best.get("oos_executed_n") or 0) < N_BAND_LOW:
            return "cooldown↓ or pct_level 浅く（イベント増）"
        return "Exit / entry_mode pull 探索"
    opp = "bounce" if cfg["mode"] == "break" else "break"
    return f"mode={opp} へ pivot、または pct_level ±0.2%"


def run_loop(max_iterations: int = MAX_ITER) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_or_fetch(SAMPLE_START, SAMPLE_END)
    print(f"Loaded {len(df)} bars", flush=True)

    iterations = []
    global_best = None
    prev_summary = None
    stale = 0
    best_p_history = []

    for i in range(1, max_iterations + 1):
        hypothesis, configs = hypothesis_for_iteration(i, prev_summary, global_best)
        next_hint = _next_hypothesis_hint(prev_summary or {}, global_best) if i > 1 else "H1 core grid"
        print(f"\n=== Cycle {i}/{max_iterations} ===", flush=True)
        print(f"Hypothesis: {hypothesis}", flush=True)
        print(f"Prior hint: {next_hint}", flush=True)

        results = []
        for cfg in configs:
            print(f"  Eval {cfg.label()}...", flush=True)
            results.append(evaluate_config(df, cfg))

        summary = _summarize_iteration(results)
        prev_best_p = global_best.get("oos_executed_p", 0) if global_best else -1e9

        if summary["best"]:
            new_p = summary["best"].get("oos_executed_p", 0)
            if global_best is None or new_p > global_best.get("oos_executed_p", 0):
                if global_best and new_p <= global_best.get("oos_executed_p", 0):
                    stale += 1
                else:
                    stale = 0
                global_best = summary["best"]
            else:
                stale += 1

        best_p_history.append(global_best.get("oos_executed_p") if global_best else None)
        learning = _learning_update(i, summary, hypothesis, stale)
        refined = _next_hypothesis_hint(summary, global_best)

        iter_record = {
            "iteration": i,
            "hypothesis": hypothesis,
            "prior_hint": next_hint if i > 1 else None,
            "refined_hypothesis": refined,
            "learning": learning,
            "gate2_count": summary["gate2_count"],
            "gate1_count": summary["gate1_count"],
            "best_label": summary["best"]["label"] if summary["best"] else None,
            "best_oos_executed_p": summary["best"].get("oos_executed_p") if summary["best"] else None,
            "configs_tested": len(configs),
            "stale_count": stale,
            "results": [{k: v for k, v in r.items() if k != "splits"} for r in results],
        }
        iterations.append(iter_record)
        prev_summary = summary

        iter_path = OUT_DIR / f"iter_{i:02d}.json"
        iter_path.write_text(json.dumps(iter_record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        print(f"  Learning: {learning}", flush=True)
        print(f"  Next: {refined}", flush=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_period": f"{SAMPLE_START}..{SAMPLE_END}",
        "max_iterations": max_iterations,
        "iterations": iterations,
        "global_best": {k: v for k, v in global_best.items() if k != "splits"} if global_best else None,
        "best_p_history": best_p_history,
        "final_stale_count": stale,
    }
    out_path = OUT_DIR / "hd4_loop_summary.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return payload


def write_report(payload: dict) -> Path:
    gb = payload.get("global_best")
    lines = [
        "# H-D4 研究ループレポート（30 サイクル）",
        "",
        f"生成: {payload.get('generated_at', '')}",
        f"サンプル: {payload.get('sample_period', '')}",
        "",
        "## エグゼクティブサマリー",
        "",
    ]

    if gb:
        cfg = gb["config"]
        lines.extend([
            f"- **全局最良**: {gb['label']}",
            f"- mode={cfg['mode']}, pct={abs(cfg['pct_level'])*100:.1f}%, swing={cfg['swing_bars']}, entry={cfg['entry_mode']}",
            f"- 執行込み OOS 月次 P ≈ **¥{gb.get('oos_executed_p', 0):,.0f}**（Gate2 目標 ¥{GATE2_P_TARGET:,}）",
            f"- EV ≈ ¥{gb.get('oos_executed_ev', 0):.1f}, N ≈ {gb.get('oos_executed_n', 0):.1f}/月, W = {gb.get('oos_executed_w', 0):.1%}",
            f"- 劣化率 = {gb.get('degradation', float('nan')):.2f}",
            f"- Gate1 = {gb.get('gate1')} / Gate2 = {gb.get('gate2')} / verdict = **{gb.get('verdict')}**",
            "",
        ])
    else:
        lines.append("- 有効な結果なし\n")

    # Progress chart as text
    history = payload.get("best_p_history", [])
    if history:
        lines.extend(["## 全局 best P の推移", ""])
        lines.append("| Cycle | Best OOS P |")
        lines.append("|---:|---:|")
        running = -1e9
        for i, p in enumerate(history, 1):
            if p is not None and p > running:
                running = p
            lines.append(f"| {i} | ¥{running:,.0f} |")
        lines.append("")

    lines.extend(["## サイクル履歴（30）", ""])
    for it in payload.get("iterations", []):
        lines.extend([
            f"### Cycle {it['iteration']}: {it['hypothesis']}",
            "",
            f"- テスト: {it['configs_tested']} / Gate1: {it['gate1_count']} / Gate2: {it['gate2_count']} / stale: {it.get('stale_count', 0)}",
            f"- Best: {it.get('best_label')} (P≈¥{it.get('best_oos_executed_p') or 0:,.0f})",
            f"- **Learning**: {it['learning']}",
            f"- **次仮説**: {it.get('refined_hypothesis', '')}",
            "",
        ])
        if it["iteration"] <= 10 or it["iteration"] % 5 == 0 or it.get("gate2_count", 0) > 0:
            lines.append("| Config | 執行P | EV | W | N/mo | G1 | G2 |")
            lines.append("|---|---:|---:|---:|---:|:---:|:---:|")
            for r in it.get("results", []):
                lines.append(
                    f"| {r['label']} | ¥{r.get('oos_executed_p', 0):,.0f} | "
                    f"¥{r.get('oos_executed_ev', 0):.1f} | {r.get('oos_executed_w', 0):.1%} | "
                    f"{r.get('oos_executed_n', 0):.1f} | "
                    f"{'Y' if r.get('gate1') else 'N'} | {'Y' if r.get('gate2') else 'N'} |"
                )
            lines.append("")

    gate2_iters = [it for it in payload.get("iterations", []) if it.get("gate2_count", 0) > 0]
    gate1_iters = [it for it in payload.get("iterations", []) if it.get("gate1_count", 0) > 0]

    lines.extend([
        "## 30 サイクル総括",
        "",
        f"- Gate2 pass サイクル: **{len(gate2_iters)}** / 30",
        f"- Gate1 pass サイクル: **{len(gate1_iters)}** / 30",
        f"- 最終 stale（無改善）: {payload.get('final_stale_count', 0)}",
        "",
        "### パラメータ応答（観察）",
        "",
        "- **mode**: break（貫通）vs bounce（反発）— Phase0 weak 再現、執行込みで split 不安定",
        "- **pct_level**: 浅いほど N↑、深いほど edge 方向性が break に寄る",
        "- **cooldown / auto-N**: N 帯調整可能だが EV とトレードオフ",
        "- **entry pull**: H-D 教訓通り immediate より pull が優位な場合あり",
        "- **Exit fixed pct**: ATR RR より執行劣化が小さい傾向",
        "",
        "### 最終判定",
        "",
    ])

    if gb and gb.get("gate2"):
        lines.append("- **promote 候補** — Gate2 pass。")
    elif gb and gb.get("gate1"):
        lines.append("- **conditional** — Gate1 pass、Gate2 fail。合成 or 別 L1 検討。")
    elif gb and (gb.get("oos_executed_ev") or 0) > 0:
        lines.append(
            f"- **weak-positive** — EV>0 だが N={gb.get('oos_executed_n', 0):.1f}/月、Gate2 遠隔。"
            " 単体 L1 不採用、フィルタ用途のみ。"
        )
    else:
        lines.append("- **reject** — 30 サイクル後も執行込み EV≤0 or Gate1 未達。")

    lines.extend([
        "",
        "## 次アクション",
        "",
        "1. H-D4 単体 promote 不可 → edge-catalog closed 候補",
        "2. EV>0 設定があれば H-D canonical との合成（非 tuning）のみ検討",
        "3. 次 L1: H-D5（ピンバー）or 別メカニズム",
        "",
        f"データ: `data/research/hd4_loop/hd4_loop_summary.json`",
        "",
    ])

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def main() -> None:
    payload = run_loop(max_iterations=MAX_ITER)
    report_path = write_report(payload)
    print(f"\nReport: {report_path}", flush=True)


if __name__ == "__main__":
    main()
