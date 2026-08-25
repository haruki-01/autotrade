#!/usr/bin/env python3
"""Run 30 SPOT-001 verification cycles (DB-22..DB-51), formal Set B only."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "eval" / "reports" / "20260823-double-bottom-30-cycles.md"
OUT_JSON = ROOT / "eval" / "reports" / "20260823-double-bottom-30-cycles.json"
WS = ROOT / "docs" / "workstreams" / "SPOT-001-double-bottom"

# Pre-declared: 1 knob from 1H/15m/4h bases. No stacking (DB-21 lesson).
CYCLES: list[dict] = [
    {"n": 22, "logic": "db_1h_up_only_v1", "knob": "1H+上昇", "why": "DB-21積は失敗。上昇フィルタ単体を1Hで見る。"},
    {"n": 23, "logic": "db_1h_not_down_v1", "knob": "1H+下降以外", "why": "上昇のみとの差。"},
    {"n": 24, "logic": "db_1h_reclaim_v1", "knob": "1H+高値奪還", "why": "4HでEV+だった反発定義を1H単体で。"},
    {"n": 25, "logic": "db_1h_fresh48_v1", "knob": "1H+鮮度48h", "why": "鮮度単体。"},
    {"n": 26, "logic": "db_1h_fresh24_v1", "knob": "1H+鮮度24h", "why": "より厳しい鮮度。"},
    {"n": 27, "logic": "db_1h_fresh72_v1", "knob": "1H+鮮度72h", "why": "緩い鮮度。"},
    {"n": 28, "logic": "db_1h_trail_v1", "knob": "1H+ATRトレール", "why": "大勝ちを残す退出。"},
    {"n": 29, "logic": "db_1h_stop_bottom_v1", "knob": "1H+第2底損切", "why": "構造損切。"},
    {"n": 30, "logic": "db_1h_tight_v1", "knob": "1H+厳しい2底", "why": "形の質。"},
    {"n": 31, "logic": "db_1h_wide_v1", "knob": "1H+緩い2底", "why": "サンプル増。"},
    {"n": 32, "logic": "db_1h_wick_v1", "knob": "1H+ヒゲ突破", "why": "突破定義。"},
    {"n": 33, "logic": "db_1h_clean_v1", "knob": "1H+きれい突破", "why": "弱い突破排除。"},
    {"n": 34, "logic": "db_1h_fixed_pct_v1", "knob": "1H+固定%反発", "why": "反発対照。"},
    {"n": 35, "logic": "db_1h_pct_height_v1", "knob": "1H+高%戻し", "why": "DB-20から上昇フィルタを外した単体。"},
    {"n": 36, "logic": "db_1h_break_bh_v1", "knob": "1H+反発高抜け", "why": "遅延エントリー。"},
    {"n": 37, "logic": "db_1h_first_retest_v1", "knob": "1H+初回のみ", "why": "二度目以降を捨てる。"},
    {"n": 38, "logic": "db_1h_session_v1", "knob": "1H+セッション", "why": "薄い時間回避。"},
    {"n": 39, "logic": "db_1h_pivot2_v1", "knob": "1H+ピボット2", "why": "検出感度↑。"},
    {"n": 40, "logic": "db_1h_pivot5_v1", "knob": "1H+ピボット5", "why": "検出感度↓。"},
    {"n": 41, "logic": "db_1h_band_tight_v1", "knob": "1H+帯狭い", "why": "ネックタッチ精度。"},
    {"n": 42, "logic": "db_1h_band_wide_v1", "knob": "1H+帯広い", "why": "タッチ取りこぼし減。"},
    {"n": 43, "logic": "db_1h_close_bottoms_v1", "knob": "1H+底近い", "why": "時間間隔。"},
    {"n": 44, "logic": "db_1h_far_bottoms_v1", "knob": "1H+底遠い", "why": "より大きなDB。"},
    {"n": 45, "logic": "db_15m_baseline_v1", "knob": "15m構造", "why": "回数確保（1m未満禁止の下限に近い）。"},
    {"n": 46, "logic": "db_15m_up_only_v1", "knob": "15m+上昇", "why": "15mに質フィルタ1点。"},
    {"n": 47, "logic": "db_15m_reclaim_v1", "knob": "15m+奪還", "why": "15mに反発定義。"},
    {"n": 48, "logic": "db_15m_fresh48_v1", "knob": "15m+鮮度", "why": "15mに鮮度。"},
    {"n": 49, "logic": "db_4h_band_tight_v1", "knob": "4H+帯狭い", "why": "4H残りノブ。"},
    {"n": 50, "logic": "db_4h_pivot2_v1", "knob": "4H+ピボット2", "why": "4H感度。"},
    {"n": 51, "logic": "db_1h_atr_stop_v1", "knob": "1H+ATR損切", "why": "損切定義の単体。"},
]


def run_eval(logic_id: str) -> dict:
    env = {**os.environ, "PYTHONPATH": "src"}
    proc = subprocess.run(
        [sys.executable, "-m", "autotrade.cli", "eval", "--logic-id", logic_id],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
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
            "stderr": (proc.stderr or "")[-2000:],
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


def main() -> int:
    WS.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    lines = [
        "# SPOT-001 ダブルボトム — 検証30サイクル（DB-22..DB-51）",
        "",
        f"実行UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "## 方針",
        "",
        "- DB-21（質ノブの積）失敗を受け、**1H/15m/4H基点でノブは1点のみ**",
        "- `min_trades=100` は **Set B 1年合計**（月次ではない）",
        "- 足は15m以上（1分未満禁止）",
        "- EMA不使用",
        "",
        "## サマリー",
        "",
        "| C# | logic | knob | Gate | EV | DD | n | failures |",
        "|----|-------|------|------|----|----|---|----------|",
    ]

    for c in CYCLES:
        print(f"=== Cycle {c['n']:02d} {c['logic']} ===", flush=True)
        r = run_eval(c["logic"])
        r.update({"cycle": c["n"], "knob": c["knob"], "why": c["why"]})
        results.append(r)
        gate = "PASS" if r.get("gate_pass") else ("ERR" if r.get("error") else "FAIL")
        ev = r.get("avg_trade_pnl")
        dd = r.get("max_drawdown_pct")
        lines.append(
            "| {n} | `{lid}` | {knob} | {gate} | {ev} | {dd} | {tr} | {fails} |".format(
                n=c["n"],
                lid=c["logic"],
                knob=c["knob"],
                gate=gate,
                ev=f"{ev:.3f}" if isinstance(ev, (int, float)) else "—",
                dd=f"{dd:.1f}%" if isinstance(dd, (int, float)) else "—",
                tr=r.get("trades", "—"),
                fails=",".join(r.get("gate_failures") or []) or ("error" if r.get("error") else "—"),
            )
        )

    lines.extend(["", "## サイクル詳細", ""])
    for r in results:
        lines.append(f"### C{r['cycle']:02d} — `{r['logic_id']}`")
        lines.append("")
        lines.append(f"- **ノブ:** {r['knob']}")
        lines.append(f"- **なぜ:** {r['why']}")
        if r.get("error"):
            lines.append(f"- **エラー:** ```\n{(r.get('stderr') or '')[:800]}\n```")
        else:
            lines.append(
                f"- **結果:** n={r.get('trades')} / EV={r.get('avg_trade_pnl')} / DD={r.get('max_drawdown_pct')} / fail={','.join(r.get('gate_failures') or []) or '—'}"
            )
            if r.get("report_path"):
                lines.append(f"- **report:** `{r['report_path']}`")
        lines.append("")

    ok = [r for r in results if not r.get("error")]
    passes = [r for r in ok if r.get("gate_pass")]
    best_ev = max(
        ok,
        key=lambda x: (x.get("avg_trade_pnl") is not None, x.get("avg_trade_pnl") or -1e9),
        default=None,
    )
    most_n = max(ok, key=lambda x: x.get("trades") or 0, default=None)
    lines.extend(
        [
            "## 総括",
            "",
            f"- Gate PASS: **{len(passes)}** / {len(results)}",
            f"- 最多n: `{most_n['logic_id'] if most_n else '—'}` n={most_n.get('trades') if most_n else '—'}",
            f"- 最良EV: `{best_ev['logic_id'] if best_ev else '—'}` EV={best_ev.get('avg_trade_pnl') if best_ev else '—'}",
            "",
            "### PASS一覧（あれば Set C へ）",
            "",
        ]
    )
    if passes:
        for p in passes:
            lines.append(
                f"- `{p['logic_id']}` EV={p.get('avg_trade_pnl')} DD={p.get('max_drawdown_pct')} n={p.get('trades')}"
            )
    else:
        lines.append("- なし")
    lines.extend(
        [
            "",
            "### 構造的学び",
            "",
            "1. 1Hに質ノブを **1点だけ**足したときの EV/n の変化を比較する（積は禁止）。",
            "2. 15m構造は回数が出やすいか、費用負けしないかを見る。",
            "3. PASSは必ず Set C holdout。ギリギリEV+は採用しない。",
            "",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_MD}", flush=True)
    return 0 if passes else 2


if __name__ == "__main__":
    raise SystemExit(main())
