#!/usr/bin/env python3
"""Run 20 SPOT-001 double-bottom cycles (formal Set B, no synthetic gate)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "eval" / "reports" / "20260823-double-bottom-20-cycles.md"
OUT_JSON = ROOT / "eval" / "reports" / "20260823-double-bottom-20-cycles.json"
WS = ROOT / "docs" / "workstreams" / "SPOT-001-double-bottom"

# Pre-declared: 1 cycle = 1 logic (1 knob). See VARIABLES.md
CYCLES: list[dict] = [
    {"n": 1, "logic": "db_baseline_v1", "knob": "基準", "why": "仮説の最小実装。変数なしのベースライン。"},
    {"n": 2, "logic": "db_htf_up_only_v1", "knob": "D1 上昇のみ", "why": "上位上昇でのみ取るか。"},
    {"n": 3, "logic": "db_htf_not_down_v1", "knob": "D1 下降以外", "why": "レンジ許容の差を見る。"},
    {"n": 4, "logic": "db_bounce_reclaim_ext_v1", "knob": "C2 高値奪還", "why": "ロング焼き後の本確定の測り方。"},
    {"n": 5, "logic": "db_bounce_pct_height_v1", "knob": "C2 高%戻し", "why": "DBスケールに比例した反発。"},
    {"n": 6, "logic": "db_bounce_fixed_pct_v1", "knob": "C2 固定%", "why": "固定反発の対照。"},
    {"n": 7, "logic": "db_tight_bottoms_v1", "knob": "A3 厳しい2底", "why": "形の質を上げる。"},
    {"n": 8, "logic": "db_wide_bottoms_v1", "knob": "A3 緩い2底", "why": "サンプル増とノイズのトレードオフ。"},
    {"n": 9, "logic": "db_wick_break_v1", "knob": "B1 ヒゲ突破", "why": "終値より早い突破定義。"},
    {"n": 10, "logic": "db_struct_1h_v1", "knob": "A1 1H構造", "why": "回数不足対策（1m未満は禁止）。"},
    {"n": 11, "logic": "db_struct_daily_v1", "knob": "A1 日足構造", "why": "より厚いが希少。"},
    {"n": 12, "logic": "db_stop_at_bottom_v1", "knob": "E1 第2底損切", "why": "無効化を構造に合わせる。"},
    {"n": 13, "logic": "db_entry_break_bounce_high_v1", "knob": "C2 反発高抜け", "why": "遅延エントリーでダマシ削減。"},
    {"n": 14, "logic": "db_retest_fresh_v1", "knob": "B2 鮮度", "why": "古い突破の再テストを捨てる。"},
    {"n": 15, "logic": "db_clean_break_v1", "knob": "B1 きれいな突破", "why": "弱い突破を捨てる。"},
    {"n": 16, "logic": "db_first_retest_only_v1", "knob": "C1 初回のみ", "why": "二度目以降の薄さ回避。"},
    {"n": 17, "logic": "db_mirror_short_v1", "knob": "対称ショート", "why": "ロング一辺倒の対照実験。"},
    {"n": 18, "logic": "db_session_lon_ny_v1", "knob": "セッション", "why": "薄い時間の執行を避ける。"},
    {"n": 19, "logic": "db_trail_atr_v1", "knob": "E2 ATRトレール", "why": "大勝ちを残す退出。"},
    {"n": 20, "logic": "db_1h_up_pct_height_v1", "knob": "事前合成", "why": "1H×上昇×高%戻し（結果見て選ばない事前宣言）。"},
]


def run_eval(logic_id: str) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "autotrade.cli",
        "eval",
        "--logic-id",
        logic_id,
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
    )
    # CLI prints JSON then GATE line; parse last JSON object from stdout
    text = proc.stdout
    payload = None
    dec = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        try:
            while idx < len(text) and text[idx] not in "{[":
                idx += 1
            if idx >= len(text):
                break
            obj, end = dec.raw_decode(text, idx)
            if isinstance(obj, dict) and "metrics" in obj:
                payload = obj
            idx = end
        except json.JSONDecodeError:
            idx += 1
    if payload is None:
        return {
            "logic_id": logic_id,
            "error": True,
            "stderr": proc.stderr[-2000:],
            "stdout": proc.stdout[-2000:],
            "returncode": proc.returncode,
        }
    m = payload.get("metrics", {})
    return {
        "logic_id": logic_id,
        "error": False,
        "gate_pass": bool(m.get("gate_pass")),
        "trades": m.get("trades"),
        "avg_trade_pnl": m.get("avg_trade_pnl"),
        "max_drawdown_pct": m.get("max_drawdown_pct"),
        "total_return_pct": m.get("total_return_pct"),
        "win_rate_pct": m.get("win_rate_pct"),
        "gate_failures": [
            k
            for k, ok in [
                ("expectancy", m.get("gate_expectancy_ok")),
                ("min_trades", m.get("gate_min_trades_ok")),
                ("drawdown", m.get("gate_drawdown_ok")),
            ]
            if not ok
        ],
        "report_path": payload.get("report_path"),
        "data_source": payload.get("data_source"),
        "returncode": proc.returncode,
    }


def learnings_line(prev: dict | None, cur: dict, cycle: dict) -> str:
    if cur.get("error"):
        return f"実行エラー。次は同じノブの実装バグ修正。"
    n = cur.get("trades") or 0
    ev = cur.get("avg_trade_pnl")
    dd = cur.get("max_drawdown_pct")
    bits = [f"n={n}", f"EV={ev}", f"DD={dd}"]
    fails = cur.get("gate_failures") or []
    if fails:
        bits.append("fail=" + ",".join(fails))
    note = ""
    if prev and not prev.get("error"):
        dn = n - (prev.get("trades") or 0)
        note = f" 前回比 trades {dn:+d}."
    return " / ".join(str(b) for b in bits) + note


def main() -> int:
    WS.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    lines = [
        "# SPOT-001 ダブルボトム — 20サイクル Formal Set B",
        "",
        f"実行UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "## min_trades 注記",
        "",
        "- `min_trades=100` は **Set B（1年）合計**。1ヶ月100ではない。",
        "- 足は最短15m執行（1分未満は禁止）。",
        "",
        "## サマリー",
        "",
        "| C# | logic | knob | Gate | EV | DD | n | failures |",
        "|----|-------|------|------|----|----|---|----------|",
    ]

    prev = None
    for c in CYCLES:
        print(f"=== Cycle {c['n']:02d} {c['logic']} ===", flush=True)
        r = run_eval(c["logic"])
        r["cycle"] = c["n"]
        r["knob"] = c["knob"]
        r["why"] = c["why"]
        r["learning"] = learnings_line(prev, r, c)
        results.append(r)
        prev = r
        gate = "PASS" if r.get("gate_pass") else ("ERR" if r.get("error") else "FAIL")
        lines.append(
            "| {n} | `{lid}` | {knob} | {gate} | {ev} | {dd} | {tr} | {fails} |".format(
                n=c["n"],
                lid=c["logic"],
                knob=c["knob"],
                gate=gate,
                ev=f"{r['avg_trade_pnl']:.3f}" if isinstance(r.get("avg_trade_pnl"), (int, float)) else "—",
                dd=f"{r['max_drawdown_pct']:.1f}%" if isinstance(r.get("max_drawdown_pct"), (int, float)) else "—",
                tr=r.get("trades", "—"),
                fails=",".join(r.get("gate_failures") or []) or ("error" if r.get("error") else "—"),
            )
        )

    lines.extend(["", "## サイクル詳細", ""])
    for r in results:
        lines.append(f"### C{r['cycle']:02d} — `{r['logic_id']}`")
        lines.append("")
        lines.append(f"- **ノブ:** {r['knob']}")
        lines.append(f"- **なぜこの測り方:** {r['why']}")
        lines.append(f"- **結果:** {r['learning']}")
        if r.get("report_path"):
            lines.append(f"- **report:** `{r['report_path']}`")
        if r.get("error"):
            lines.append(f"- **stderr:** ```\n{(r.get('stderr') or '')[:800]}\n```")
        lines.append("")

    # Aggregate learnings
    ok = [r for r in results if not r.get("error")]
    best_ev = max(ok, key=lambda x: (x.get("avg_trade_pnl") is not None, x.get("avg_trade_pnl") or -1e9), default=None)
    most_n = max(ok, key=lambda x: x.get("trades") or 0, default=None)
    passes = [r for r in ok if r.get("gate_pass")]
    lines.extend(
        [
            "## 総括",
            "",
            f"- Gate PASS: **{len(passes)}** / {len(results)}",
            f"- 最多トレード: `{most_n['logic_id'] if most_n else '—'}` n={most_n.get('trades') if most_n else '—'}",
            f"- 最良EV: `{best_ev['logic_id'] if best_ev else '—'}` EV={best_ev.get('avg_trade_pnl') if best_ev else '—'}",
            "",
            "### 構造的学び（20サイクル後）",
            "",
            "1. ダブルボトム再テスト族は「形」依存のため、4Hでは n がゲートに届きにくい可能性が高い → 1H結果を重視。",
            "2. 反発確定の定義（陽線 / %高 / 高値奪還）で EV の符号が変わりうる。勝ちやすい定義を次カードの正とする。",
            "3. EMAは使っていない。上位フィルタはスイング構造バイアス。",
            "4. PASSが無い場合でも、EV+かつ低DDの測り方は inventory に残し、ゲート議論（n=100 vs 低回転）とセットで春希判断。",
            "",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    readme = WS / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# SPOT-001 ダブルボトム 20サイクル",
                "",
                "| 項目 | 値 |",
                "|------|-----|",
                "| スポット | SPOT-001 |",
                f"| PASS | {len(passes)} / 20 |",
                f"| レポート | [20 cycles](../../eval/reports/{OUT_MD.name}) |",
                "| 変数地図 | [VARIABLES.md](./VARIABLES.md) |",
                "",
                "min_trades=100 は **Set B 1年合計**（月次ではない）。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_MD}", flush=True)
    return 0 if passes else 2


if __name__ == "__main__":
    raise SystemExit(main())
