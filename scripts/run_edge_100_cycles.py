#!/usr/bin/env python3
"""Run the 100 EH-01..EH-10 verification cycles on locked formal-eval data.

The 100 logics are pre-declared in ``autotrade.strategy.edge.CYCLE_EDGE``
(10 per hypothesis, one knob each, controls included). Frames and derivative
context are loaded once per set, then every logic is scored in-process.

Usage:
    python3 scripts/run_edge_100_cycles.py --set B
    python3 scripts/run_edge_100_cycles.py --set C --logics eh01_base,eh02_base
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autotrade.backtest.engine import run_backtest, trades_to_frame  # noqa: E402
from autotrade.backtest.metrics import compute_metrics, metrics_to_dict  # noqa: E402
from autotrade.eval import (  # noqa: E402
    LOCK_PATH,
    load_eval_config,
    load_locked_derivatives,
    load_locked_frames,
    validate_lock,
)
from autotrade.research.log import record_backtest_run  # noqa: E402
from autotrade.strategy.edge import CYCLE_EDGE as _CYCLE_EDGE, prepare_frames  # noqa: E402
from autotrade.strategy.edge_refine import CYCLE_EDGE_R as _CYCLE_EDGE_R  # noqa: E402
from autotrade.strategy.registry import LOGIC_META  # noqa: E402

# The original 100 plus the refinement packs; both use the same param object.
CYCLE_EDGE = {**_CYCLE_EDGE, **_CYCLE_EDGE_R}

CONFIG = ROOT / "configs" / "eval_v1.yaml"


def score_one(
    logic_id: str,
    m15: pd.DataFrame,
    deriv: pd.DataFrame,
    cfg,
    set_name: str,
    *,
    artifacts_root: Path,
) -> dict:
    params, hyp, name, knob, why = CYCLE_EDGE[logic_id]
    prepared = prepare_frames(m15, deriv, params)
    lo = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
    hi = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
    window = prepared[(prepared.index >= lo) & (prepared.index < hi)]
    if window.empty:
        return {"logic_id": logic_id, "error": "no bars in window"}

    result = run_backtest(
        window,
        initial_equity=cfg.initial_equity,
        leverage=cfg.leverage,
        risk_per_trade_pct=cfg.risk_per_trade_pct,
        stop_loss_pct=cfg.stop_loss_pct,
        take_profit_pct=cfg.take_profit_pct,
        fee_rate=cfg.fee_rate_per_side,
        slippage_pct=cfg.slippage_pct_per_side,
        sizing_mode=cfg.sizing_mode,
        margin_per_trade=cfg.margin_per_trade,
        risk_per_trade_usdt=cfg.risk_per_trade_usdt,
    )
    m = compute_metrics(
        result, min_trades=cfg.min_trades, max_drawdown_pct_limit=cfg.max_drawdown_pct
    )
    md = metrics_to_dict(m)

    out_dir = artifacts_root / f"set{set_name}_{logic_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    trades_to_frame(result.trades).to_csv(out_dir / "trades.csv", index=False)
    result.equity_curve.to_csv(out_dir / "equity_curve.csv", header=True)
    (out_dir / "metrics.json").write_text(json.dumps(md, indent=2), encoding="utf-8")

    return {
        "logic_id": logic_id,
        "hypothesis_id": hyp,
        "family": params.family,
        "knob": knob,
        "why": why,
        "set": set_name,
        "signals_long": int(window["long_signal"].sum()),
        "signals_short": int(window["short_signal"].sum()),
        "trades": md["trades"],
        "long_trades": md["long_trades"],
        "short_trades": md["short_trades"],
        "avg_trade_pnl": md["avg_trade_pnl"],
        "total_return_pct": md["total_return_pct"],
        "max_drawdown_pct": md["max_drawdown_pct"],
        "win_rate_pct": md["win_rate_pct"],
        "payoff_ratio": md["payoff_ratio"],
        "total_fees": md["total_fees"],
        "total_funding": md["total_funding"],
        "gate_pass": md["gate_pass"],
        "gate_failures": [
            k
            for k, ok in [
                ("expectancy", md["gate_expectancy_ok"]),
                ("min_trades", md["gate_min_trades_ok"]),
                ("drawdown", md["gate_drawdown_ok"]),
            ]
            if not ok
        ],
        "artifacts_dir": str(out_dir.as_posix()),
        "_metrics": md,
        "_final_equity": result.final_equity,
    }


def _fmt(v, spec: str = ".3f") -> str:
    return format(v, spec) if isinstance(v, (int, float)) else "—"


def write_report(rows: list[dict], set_name: str, out_md: Path, source: str) -> None:
    ok = [r for r in rows if "error" not in r]
    passes = [r for r in ok if r["gate_pass"]]
    lines = [
        f"# EH-01〜EH-10 — 検証100サイクル（Set {set_name}）",
        "",
        f"実行UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}  ",
        f"データ: {source} / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  ",
        "コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加",
        "",
        "## 方針",
        "",
        "- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める",
        "- 合否は差の読み取りに使う。単体のEVだけでは採用しない",
        "- `min_trades=100` は Set B 1年合計。足は15分",
        "",
        "## サマリー",
        "",
        f"- Gate PASS: **{len(passes)} / {len(ok)}**",
        "",
        "| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |",
        "|---|-------|------|------|------|---|-----|-----|------|----------|------------|",
    ]
    for i, r in enumerate(rows, 1):
        if "error" in r:
            lines.append(f"| {i} | `{r['logic_id']}` | — | — | ERR | — | — | — | — | — | {r['error']} |")
            continue
        lines.append(
            "| {i} | `{lid}` | {hyp} | {knob} | {gate} | {n} | {ev} | {dd} | {wr} | {fund} | {fails} |".format(
                i=i,
                lid=r["logic_id"],
                hyp=r["hypothesis_id"],
                knob=r["knob"],
                gate="PASS" if r["gate_pass"] else "FAIL",
                n=r["trades"],
                ev=_fmt(r["avg_trade_pnl"]),
                dd=_fmt(r["max_drawdown_pct"], ".1f"),
                wr=_fmt(r["win_rate_pct"], ".1f"),
                fund=_fmt(r["total_funding"], ".1f"),
                fails=",".join(r["gate_failures"]) or "—",
            )
        )

    lines += ["", "## 仮説ごとの読み取り（本命 vs 対照）", ""]
    for hyp in sorted({r["hypothesis_id"] for r in ok}):
        group = [r for r in ok if r["hypothesis_id"] == hyp]
        base = next((r for r in group if r["logic_id"].endswith("_base")), None)
        ctrls = [r for r in group if "_ctrl_" in r["logic_id"]]
        lines.append(f"### {hyp}")
        lines.append("")
        lines.append("| 役割 | logic | n | EV$ | DD% |")
        lines.append("|------|-------|---|-----|-----|")
        if base:
            lines.append(
                f"| 本命 | `{base['logic_id']}` | {base['trades']} | {_fmt(base['avg_trade_pnl'])} | {_fmt(base['max_drawdown_pct'], '.1f')} |"
            )
        for c in ctrls:
            lines.append(
                f"| 対照 | `{c['logic_id']}` | {c['trades']} | {_fmt(c['avg_trade_pnl'])} | {_fmt(c['max_drawdown_pct'], '.1f')} |"
            )
        if base and ctrls:
            deltas = [
                f"`{c['logic_id']}` 比 {base['avg_trade_pnl'] - c['avg_trade_pnl']:+.3f}"
                for c in ctrls
                if isinstance(c["avg_trade_pnl"], (int, float))
            ]
            lines.append("")
            lines.append("本命−対照のEV差: " + " / ".join(deltas))
        best = max(group, key=lambda r: r["avg_trade_pnl"] if r["trades"] >= 30 else -1e9)
        lines.append("")
        lines.append(
            f"n≥30で最良EV: `{best['logic_id']}` EV={_fmt(best['avg_trade_pnl'])} n={best['trades']}"
        )
        lines.append("")

    lines += ["## PASS一覧", ""]
    if passes:
        for p in sorted(passes, key=lambda r: -r["avg_trade_pnl"]):
            lines.append(
                f"- `{p['logic_id']}` ({p['hypothesis_id']}) EV={_fmt(p['avg_trade_pnl'])} n={p['trades']} DD={_fmt(p['max_drawdown_pct'], '.1f')}%"
            )
    else:
        lines.append("- なし")
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="B", choices=["A", "B", "C"])
    ap.add_argument("--logics", default=None, help="Comma-separated subset")
    ap.add_argument(
        "--pack",
        default="edge100",
        choices=["edge100", "refine", "all"],
        help="Which pre-declared pack to run when --logics is not given",
    )
    ap.add_argument("--tag", default=None, help="Report filename tag")
    ap.add_argument("--no-research-log", action="store_true")
    args = ap.parse_args()

    cfg, policy, _ = load_eval_config(CONFIG)
    lock = yaml.safe_load(LOCK_PATH.read_text(encoding="utf-8"))
    errors = validate_lock(lock, config_path=CONFIG, set_name=args.set)
    if errors:
        print("Eval environment invalid:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1

    frames, source = load_locked_frames(lock, args.set)
    m15 = frames["15m"]
    deriv = load_locked_derivatives(lock, args.set, m15.index)
    print(f"set={args.set} source={source} bars={len(m15)} deriv={deriv.shape}", flush=True)

    if args.logics:
        logic_ids = [x.strip() for x in args.logics.split(",") if x.strip()]
    elif args.pack == "refine":
        logic_ids = list(_CYCLE_EDGE_R.keys())
    elif args.pack == "all":
        logic_ids = list(CYCLE_EDGE.keys())
    else:
        logic_ids = list(_CYCLE_EDGE.keys())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_root = ROOT / "artifacts" / "evals" / f"{stamp}_edge100_set{args.set}"

    rows: list[dict] = []
    for i, lid in enumerate(logic_ids, 1):
        try:
            r = score_one(lid, m15, deriv, cfg, args.set, artifacts_root=artifacts_root)
        except Exception as exc:  # noqa: BLE001
            r = {"logic_id": lid, "error": f"{type(exc).__name__}: {exc}"}
        rows.append(r)
        if "error" in r:
            print(f"[{i:3d}/{len(logic_ids)}] {lid:26s} ERROR {r['error']}", flush=True)
        else:
            print(
                f"[{i:3d}/{len(logic_ids)}] {lid:26s} "
                f"{'PASS' if r['gate_pass'] else 'FAIL'} n={r['trades']:4d} "
                f"EV={r['avg_trade_pnl']:+.3f} DD={r['max_drawdown_pct']:.1f}%",
                flush=True,
            )

    tag = args.tag or f"edge-100-cycles-set{args.set}"
    out_md = ROOT / "eval" / "reports" / f"{datetime.now(timezone.utc):%Y%m%d}-{tag}.md"
    out_json = out_md.with_suffix(".json")
    write_report(rows, args.set, out_md, source)
    out_json.write_text(
        json.dumps(
            [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if not args.no_research_log:
        for r in rows:
            if "error" in r or not r["gate_pass"]:
                continue
            meta = LOGIC_META[r["logic_id"]]
            payload = {
                "mode": "formal_eval",
                "eval_version": policy.eval_version,
                "set": args.set,
                "config": str(CONFIG.relative_to(ROOT).as_posix()),
                "logic_id": r["logic_id"],
                "hypothesis_id": r["hypothesis_id"],
                "eval_start": cfg.sets[args.set].start,
                "eval_end": cfg.sets[args.set].end,
                "synthetic": False,
                "data_source": source,
                "metrics": r["_metrics"],
                "final_equity": r["_final_equity"],
                "gate_pass": True,
            }
            record_backtest_run(
                payload=payload,
                artifacts_dir=Path(r["artifacts_dir"]),
                hypothesis_id=r["hypothesis_id"],
                logic_id=r["logic_id"],
                hypothesis_name=meta["name"],
                distortion_ids=list(meta.get("distortion_ids") or []),
                logic_summary={"knob": r["knob"], "family": r["family"], "cycle_pack": "edge_100"},
                learnings={
                    "one_liner": f"Set {args.set} ゲート合格（100サイクル）",
                    "summary": f"{r['why']} n={r['trades']} EV={r['avg_trade_pnl']:.3f}",
                    "keep": ["価格外データ（OI/funding/basis/成行）を条件に使う"],
                    "discard": ["対照との差を見ずに単体EVで採用すること"],
                },
                next_actions=["Set C holdout", "対照との差を確認"],
                notes="edge_100 batch",
            )

    ok = [r for r in rows if "error" not in r]
    passes = [r for r in ok if r["gate_pass"]]
    print(f"\nPASS {len(passes)}/{len(ok)}  →  {out_md}", flush=True)
    for p in passes:
        print(f"  {p['logic_id']}  EV={p['avg_trade_pnl']:+.3f} n={p['trades']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
