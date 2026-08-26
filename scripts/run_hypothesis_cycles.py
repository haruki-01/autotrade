#!/usr/bin/env python3
"""Run 10 hypothesis cycles: select → formal eval Set B → update notes.

Each cycle evaluates 3–5 logics. Does NOT use synthetic for pass/fail.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval" / "reports" / "20260822-hypothesis-10-cycles.md"
STATE = ROOT / "eval" / "reports" / "20260822-hypothesis-10-cycles.json"

# Pre-declared packs; later cycles' "why" text is filled after earlier results in the report.
CYCLES: list[dict] = [
    {
        "n": 1,
        "theme": "R4H/BM データ逆算本命",
        "select_why": "前回終了時点の次アクション。Discovery上位の4Hスポットを一気に検証。",
        "logics": [
            "h4_break_non_asia_v1",
            "h4_break_london_v1",
            "h4_shallow_pb_exp_v1",
            "h4_bm_entry_v1",
            "h4_half_pb_london_v1",
        ],
    },
    {
        "n": 2,
        "theme": "セッション対照 + D-004系",
        "select_why": "C1の結果を見てセッション差（NY/アジア対照）と失敗下抜け回復を検証。",
        "logics": [
            "h4_break_ny_v1",
            "h4_break_asia_only_v1",
            "h4_fail_ll_reclaim_v1",
            "h4_near_high_exp_lon_v1",
        ],
    },
    {
        "n": 3,
        "theme": "継続・突破後押し・二度目",
        "select_why": "初動突破が弱い場合、継続/押し/二度目の測り方へ更新。",
        "logics": [
            "h4_pb_after_break_v1",
            "h4_exp_trend_cont_v1",
            "h4_compress_break_lon_v1",
            "d_second_break_v1",
        ],
    },
    {
        "n": 4,
        "theme": "日足DEEP（D-002/003/押しの質）",
        "select_why": "4Hが全滅寄りなら日足の深いスポット測り方を検証。",
        "logics": [
            "d_reclaim_deep_v1",
            "d_break_not_compress_v1",
            "d_shallow_pb_v1",
            "d_half_pb_v1",
        ],
    },
    {
        "n": 5,
        "theme": "ショート/フェードと頻度解放",
        "select_why": "ロング一辺倒の更新。下方向・フェード・フィルタ薄を対照。",
        "logics": [
            "h4_dn_break_non_asia_v1",
            "h4_fade_asia_high_v1",
            "d_dn_break_v1",
            "d_break_any_v1",
        ],
    },
    {
        "n": 6,
        "theme": "曜日・ボラレジーム",
        "select_why": "カレンダーと圧縮/拡大レジームでブレイクの質を分解。",
        "logics": [
            "d_monday_break_v1",
            "d_fri_break_v1",
            "d_exp_break_v1",
            "d_comp_break_v1",
        ],
    },
    {
        "n": 7,
        "theme": "初回vs再突破・レンジ位置",
        "select_why": "D-001/002の示唆（初回より再/位置）を4Hで検証。",
        "logics": [
            "h4_repeat_break_v1",
            "h4_first_break_v1",
            "h4_mid_range_break_v1",
            "h4_two_bull_high_v1",
        ],
    },
    {
        "n": 8,
        "theme": "回帰・カウンター・確認足",
        "select_why": "トレンド追随が弱い場合の回復・逆行・陽線確認。",
        "logics": [
            "h4_low_reclaim_v1",
            "h4_break_below_sma_v1",
            "d_near_high_break_v1",
            "h4_break_bull_confirm_v1",
        ],
    },
    {
        "n": 9,
        "theme": "C1有望系のセッション/ボラ絞り",
        "select_why": "相対的にマシだった押し×拡大・BM・非アジアをセッション/ボラで新カード化（同値再チューニング禁止）。",
        "logics": [
            "h4_shallow_pb_exp_lon_v1",
            "h4_shallow_pb_exp_ny_v1",
            "h4_bm_not_asia_v1",
            "h4_break_non_asia_exp_v1",
        ],
    },
    {
        "n": 10,
        "theme": "圧縮対照・曜日・構造パターン",
        "select_why": "最終パック。圧縮突破・火水木・インサイド・NY回復で地図を閉じる。",
        "logics": [
            "h4_break_non_asia_comp_v1",
            "h4_break_midweek_v1",
            "h4_inside_bar_break_v1",
            "h4_fail_ll_reclaim_ny_v1",
        ],
    },
]


def run_eval(logic_id: str) -> dict:
    import os

    cmd = [
        sys.executable,
        "-m",
        "autotrade.cli",
        "eval",
        "--logic-id",
        logic_id,
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    text = proc.stdout
    data = None
    if "{" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                data = None
    if data is None:
        return {
            "logic_id": logic_id,
            "error": True,
            "stderr": (proc.stderr or "")[-800:],
            "stdout_tail": text[-800:],
            "returncode": proc.returncode,
            "gate_pass": False,
        }
    m = data.get("metrics", {})
    return {
        "logic_id": logic_id,
        "hypothesis_id": data.get("hypothesis_id"),
        "gate_pass": bool(data.get("gate_pass")),
        "trades": m.get("trades"),
        "avg_trade_pnl": m.get("avg_trade_pnl"),
        "max_drawdown_pct": m.get("max_drawdown_pct"),
        "total_return_pct": m.get("total_return_pct"),
        "win_rate_pct": m.get("win_rate_pct"),
        "report_path": data.get("report_path"),
        "error": False,
        "returncode": proc.returncode,
    }


def update_note(cycle: dict, results: list[dict]) -> str:
    passes = [r for r in results if r.get("gate_pass")]
    best = None
    scored = [r for r in results if not r.get("error") and r.get("trades") is not None]
    if scored:
        best = max(
            scored,
            key=lambda r: (
                (r.get("avg_trade_pnl") or -999),
                (r.get("trades") or 0),
            ),
        )
    fail_n = sum(1 for r in results if not r.get("gate_pass"))
    lines = [
        f"### 仮説アップデート（Cycle {cycle['n']}後）",
        "",
        f"- Gate PASS: {len(passes)} / {len(results)}（FAIL {fail_n}）",
    ]
    if best:
        lines.append(
            f"- 相対ベスト: `{best['logic_id']}` "
            f"EV={best.get('avg_trade_pnl'):.2f} n={best.get('trades')} "
            f"DD={best.get('max_drawdown_pct'):.1f}%"
        )
    # Learning heuristics
    ev_pos = [r for r in scored if (r.get("avg_trade_pnl") or 0) > 0]
    n_ok = [r for r in scored if (r.get("trades") or 0) >= 100]
    if n_ok:
        lines.append("- 学び: n≥100 を満たすロジックあり → 頻度設計は前進。")
    else:
        lines.append("- 学び: 依然 n不足が主因。スポットをさらに高頻度寄りへ更新。")
    if ev_pos:
        lines.append(
            "- 学び: EV+ の芽: " + ", ".join(f"`{r['logic_id']}`" for r in ev_pos[:5])
        )
    else:
        lines.append("- 学び: このパックは費用後EVが総じて非正。方向/測り方を転換。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    all_rows: list[dict] = []
    md: list[str] = [
        "# 仮説サイクル ×10（選定→検証→更新）",
        "",
        f"- 実行UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "- 環境: `configs/eval_v1.yaml` / Set **B** / formal only（syntheticなし）",
        "- 制約: 各サイクル 3〜5ロジック",
        "",
    ]

    for cycle in CYCLES:
        assert 3 <= len(cycle["logics"]) <= 5, cycle
        md.append(f"## Cycle {cycle['n']}: {cycle['theme']}")
        md.append("")
        md.append(f"**選定理由:** {cycle['select_why']}")
        md.append("")
        md.append("| logic_id | HYP | n | EV | DD% | ret% | Gate |")
        md.append("|----------|-----|---|----|-----|------|------|")
        results = []
        for lid in cycle["logics"]:
            print(f"[Cycle {cycle['n']}] eval {lid} ...", flush=True)
            r = run_eval(lid)
            results.append(r)
            all_rows.append({"cycle": cycle["n"], **r})
            if r.get("error"):
                md.append(f"| `{lid}` | — | ERR | — | — | — | FAIL |")
            else:
                gate = "PASS" if r["gate_pass"] else "FAIL"
                md.append(
                    f"| `{lid}` | {r.get('hypothesis_id')} | {r.get('trades')} | "
                    f"{r.get('avg_trade_pnl'):.2f} | {r.get('max_drawdown_pct'):.1f} | "
                    f"{r.get('total_return_pct'):.1f} | **{gate}** |"
                )
        md.append("")
        md.append(update_note(cycle, results))
        md.append("")

    # Summary tables
    md.append("## 全体サマリ")
    md.append("")
    passes = [r for r in all_rows if r.get("gate_pass")]
    md.append(f"- 検証本数: {len(all_rows)}")
    md.append(f"- Gate PASS: {len(passes)}")
    scored = [r for r in all_rows if not r.get("error") and r.get("avg_trade_pnl") is not None]
    scored_sorted = sorted(scored, key=lambda r: r["avg_trade_pnl"], reverse=True)
    md.append("")
    md.append("### EV上位（Gate問わず・参考）")
    md.append("")
    md.append("| rank | cycle | logic_id | n | EV | DD% | Gate |")
    md.append("|------|-------|----------|---|----|-----|------|")
    for i, r in enumerate(scored_sorted[:10], 1):
        md.append(
            f"| {i} | {r['cycle']} | `{r['logic_id']}` | {r['trades']} | "
            f"{r['avg_trade_pnl']:.2f} | {r['max_drawdown_pct']:.1f} | "
            f"{'PASS' if r['gate_pass'] else 'FAIL'} |"
        )
    n_sorted = sorted(scored, key=lambda r: r.get("trades") or 0, reverse=True)
    md.append("")
    md.append("### トレード数上位")
    md.append("")
    md.append("| rank | cycle | logic_id | n | EV | Gate |")
    md.append("|------|-------|----------|---|----|------|")
    for i, r in enumerate(n_sorted[:10], 1):
        md.append(
            f"| {i} | {r['cycle']} | `{r['logic_id']}` | {r['trades']} | "
            f"{r['avg_trade_pnl']:.2f} | {'PASS' if r['gate_pass'] else 'FAIL'} |"
        )

    md.append("")
    md.append("## 今後の進め方（素案）")
    md.append("")
    md.append("1. **Gate PASS が0なら**「単一条件ブレイク系」を一旦棚上げし、①スポットをチャート観察ログから作り直す（定番インジ合成の量産を止める）。")
    md.append("2. **n不足が主因のEV+芽**があれば、同じスポットのまま執行足だけ高頻度化した新カード（再チューニング禁止・定義変更）を1本だけ試す。")
    md.append("3. **EVもnもダメな系統**（例: アジア突破、圧縮一発）は撃たない仮説（E8）としてストックし、ゲート候補にする。")
    md.append("4. Discovery と Set B の乖離が大きい条件は「探索ノイズ」扱い。逆算グリッドをさらに広げない。")
    md.append("5. 次の10サイクルは「新しい①」優先。実装済みルールの組み合わせ探索は多重検定リスクが高い。")
    md.append("")
    md.append("*生成: `scripts/run_hypothesis_cycles.py`*")

    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    STATE.write_text(json.dumps({"cycles": CYCLES, "results": all_rows}, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT}", flush=True)
    print(f"PASS count: {len(passes)} / {len(all_rows)}", flush=True)


if __name__ == "__main__":
    main()
