from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("docs/research/registry.yaml")
INDEX_PATH = Path("docs/research/INDEX.md")
ENTRIES_DIR = Path("docs/research/entries")


def _git_head() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_registry(path: Path | None = None) -> dict[str, Any]:
    path = path or REGISTRY_PATH
    if not path.exists():
        return {"schema_version": 1, "runs": []}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("schema_version", 1)
    data.setdefault("runs", [])
    return data


def save_registry(data: dict[str, Any], path: Path | None = None) -> None:
    path = path or REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _next_run_id(runs: list[dict], prefix: str) -> str:
    existing = [r.get("run_id", "") for r in runs if str(r.get("run_id", "")).startswith(prefix)]
    n = len(existing) + 1
    return f"{prefix}-{n:03d}"


def _gate_failures(metrics: dict[str, Any]) -> list[str]:
    fails: list[str] = []
    if not metrics.get("gate_expectancy_ok", metrics.get("expectancy_positive")):
        fails.append("expectancy")
    if not metrics.get("gate_min_trades_ok"):
        fails.append("min_trades")
    if not metrics.get("gate_drawdown_ok"):
        fails.append("drawdown")
    return fails


def _status_from_run(*, gate_pass: bool, synthetic: bool, smoke_only: bool) -> str:
    if smoke_only or synthetic:
        return "smoke"
    if gate_pass:
        return "pass"
    return "fail"


def record_backtest_run(
    *,
    payload: dict[str, Any],
    artifacts_dir: Path,
    hypothesis_id: str,
    logic_id: str,
    hypothesis_name: str,
    distortion_ids: list[str] | None = None,
    logic_summary: dict[str, Any] | None = None,
    learnings: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Append a backtest run to registry and write a detailed entry markdown."""
    registry = load_registry()
    runs: list[dict] = registry["runs"]
    metrics = payload.get("metrics", {})
    synthetic = bool(payload.get("synthetic"))
    gate_pass = bool(metrics.get("gate_pass"))
    status = _status_from_run(
        gate_pass=gate_pass,
        synthetic=synthetic,
        smoke_only=synthetic,
    )

    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    run_id = _next_run_id(runs, date_prefix)
    recorded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry_slug = f"{hypothesis_id}-{logic_id}-set{payload.get('set')}-{date_prefix}"
    entry_path = ENTRIES_DIR / f"{entry_slug}.md"

    run_record: dict[str, Any] = {
        "run_id": run_id,
        "recorded_at": recorded_at,
        "status": status,
        "hypothesis": {
            "id": hypothesis_id,
            "logic_id": logic_id,
            "name": hypothesis_name,
            "distortion_ids": distortion_ids or [],
            "one_liner": (learnings or {}).get("one_liner", ""),
        },
        "logic": logic_summary or {},
        "test": {
            "set": payload.get("set"),
            "eval_start": payload.get("eval_start"),
            "eval_end": payload.get("eval_end"),
            "bars": payload.get("bars"),
            "data_source": payload.get("data_source"),
            "synthetic": synthetic,
            "config": payload.get("config"),
            "git_commit": _git_head(),
        },
        "results": {
            "trades": metrics.get("trades"),
            "avg_trade_pnl": metrics.get("avg_trade_pnl"),
            "total_return_pct": metrics.get("total_return_pct"),
            "monthly_return_pct_approx": metrics.get("monthly_return_pct_approx"),
            "max_drawdown_pct": metrics.get("max_drawdown_pct"),
            "win_rate_pct": metrics.get("win_rate_pct"),
            "payoff_ratio": metrics.get("payoff_ratio"),
            "total_fees": metrics.get("total_fees"),
            "long_trades": metrics.get("long_trades"),
            "short_trades": metrics.get("short_trades"),
            "final_equity": payload.get("final_equity"),
            "gate_pass": gate_pass,
            "gate_failures": _gate_failures(metrics),
        },
        "artifacts": {
            "dir": str(artifacts_dir.as_posix()),
            "metrics_json": str((artifacts_dir / "metrics.json").as_posix()),
        },
        "learnings": learnings or {},
        "next_actions": next_actions or [],
        "notes": notes or "",
        "entry_doc": str(entry_path.as_posix()),
    }

    runs.append(run_record)
    registry["runs"] = runs
    save_registry(registry)
    _write_entry_markdown(run_record, entry_path)
    refresh_index(registry)
    return run_record


def _write_entry_markdown(run: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = run["hypothesis"]
    t = run["test"]
    r = run["results"]
    lg = run.get("learnings", {})
    logic = run.get("logic", {})

    gate_icon = "PASS" if r.get("gate_pass") else "FAIL"
    if run.get("status") == "smoke":
        gate_icon = "SMOKE（判定に使わない）"

    lines = [
        f"# {h['id']} / {h['logic_id']} — Set {t.get('set')}",
        "",
        f"- **Run ID:** `{run['run_id']}`",
        f"- **記録日時:** {run['recorded_at']}",
        f"- **ステータス:** `{run['status']}`",
        f"- **ゲート:** {gate_icon}",
        "",
        "## 1. 仮説",
        "",
        f"**名称:** {h.get('name', '')}",
        "",
        f"**一言:** {h.get('one_liner') or lg.get('one_liner') or '—'}",
        "",
        f"**狙う歪み:** {', '.join(h.get('distortion_ids') or []) or '（未タグ）'}",
        "",
        "## 2. 売買ロジック",
        "",
    ]

    if logic:
        for key, val in logic.items():
            lines.append(f"- **{key}:** {val}")
    else:
        lines.append("（registry の logic フィールドを参照）")

    lines.extend(
        [
            "",
            "## 3. 検証条件",
            "",
            f"| 項目 | 値 |",
            f"|------|-----|",
            f"| 評価期間 | {t.get('eval_start')} → {t.get('eval_end')} |",
            f"| データ | {t.get('data_source')} |",
            f"| 合成データ | {t.get('synthetic')} |",
            f"| 15m本数 | {t.get('bars')} |",
            f"| 設定 | `{t.get('config')}` |",
            f"| Git | `{t.get('git_commit') or '—'}` |",
            "",
            "## 4. 結果",
            "",
            f"| 指標 | 値 |",
            f"|------|-----|",
            f"| トレード数 | {r.get('trades')} |",
            f"| 1トレード平均損益 | {r.get('avg_trade_pnl')} |",
            f"| 総リターン | {r.get('total_return_pct')}% |",
            f"| 月次換算（近似） | {r.get('monthly_return_pct_approx')}% |",
            f"| 最大DD | {r.get('max_drawdown_pct')}% |",
            f"| 勝率 | {r.get('win_rate_pct')}% |",
            f"| 最終資産 | {r.get('final_equity')} |",
            "",
            f"**ゲート不合格理由:** {', '.join(r.get('gate_failures') or []) or '—'}",
            "",
            "## 5. 知見",
            "",
        ]
    )

    if lg.get("summary"):
        lines.append(lg["summary"])
        lines.append("")
    if lg.get("structural"):
        lines.append("**構造的理由:**")
        for item in lg["structural"]:
            lines.append(f"- {item}")
        lines.append("")
    if lg.get("keep"):
        lines.append("**残す:**")
        for item in lg["keep"]:
            lines.append(f"- {item}")
        lines.append("")
    if lg.get("discard"):
        lines.append("**捨てる:**")
        for item in lg["discard"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(
        [
            "## 6. 次アクション",
            "",
        ]
    )
    for action in run.get("next_actions") or []:
        lines.append(f"- {action}")
    if not run.get("next_actions"):
        lines.append("- （未記載）")

    lines.extend(
        [
            "",
            "## 7. 成果物",
            "",
            f"- `{run['artifacts']['dir']}/`",
            f"- `{run['artifacts']['metrics_json']}`",
            "",
        ]
    )
    if run.get("notes"):
        lines.extend(["## メモ", "", run["notes"], ""])

    path.write_text("\n".join(lines), encoding="utf-8")


def refresh_index(registry: dict[str, Any] | None = None) -> None:
    registry = registry or load_registry()
    runs = sorted(registry.get("runs", []), key=lambda x: x.get("recorded_at", ""), reverse=True)

    lines = [
        "# 研究ログ — 一覧",
        "",
        "仮説・売買ロジック・検証結果の蓄積。詳細は各エントリと `registry.yaml` を参照。",
        "",
        "運用: バックテスト実行後に自動追記。手動追記は `_template.md` と `registry.yaml` を参照。",
        "",
        "## サマリー表",
        "",
        "| Run ID | 日付 | 仮説 | ロジック | Set | データ | ステータス | 期待値 | DD | トレード | 詳細 |",
        "|--------|------|------|----------|-----|--------|------------|--------|-----|----------|------|",
    ]

    for run in runs:
        h = run.get("hypothesis", {})
        t = run.get("test", {})
        r = run.get("results", {})
        entry = run.get("entry_doc", "")
        if entry:
            entry_rel = Path(entry)
            try:
                entry_rel = entry_rel.relative_to(INDEX_PATH.parent)
            except ValueError:
                pass
            link = f"[doc]({entry_rel.as_posix()})"
        else:
            link = "—"
        ds = t.get("data_source")
        ds_s = "—" if ds is None else str(ds)
        avg = r.get("avg_trade_pnl")
        avg_s = f"{avg:.2f}" if isinstance(avg, (int, float)) else "—"
        dd = r.get("max_drawdown_pct")
        dd_s = f"{dd:.1f}%" if isinstance(dd, (int, float)) else "—"
        lines.append(
            "| {run_id} | {date} | {hid} | {lid} | {set_} | {ds} | `{status}` | {avg} | {dd} | {trades} | {link} |".format(
                run_id=run.get("run_id", ""),
                date=(run.get("recorded_at") or "")[:10],
                hid=h.get("id", ""),
                lid=h.get("logic_id", ""),
                set_=t.get("set", ""),
                ds=ds_s,
                status=run.get("status", ""),
                avg=avg_s,
                dd=dd_s,
                trades=r.get("trades", ""),
                link=link,
            )
        )

    lines.extend(
        [
            "",
            "## ステータス凡例",
            "",
            "| ステータス | 意味 |",
            "|------------|------|",
            "| `pass` | Set B ゲート合格 |",
            "| `fail` | 実データでゲート不合格 |",
            "| `smoke` | 合成データ等。採用判断に使わない |",
            "| `proposed` | 未検証 |",
            "| `archived` | 参照用に残すが追わない |",
            "",
            "## 関連",
            "",
            "- [README（運用ルール）](./README.md)",
            "- [registry.yaml](./registry.yaml) — 機械可読マスタ",
            "- [エントリテンプレート](./_template.md)",
            "- [市場の歪み前提](../MARKET_EDGE_MAP.md)",
            "",
        ]
    )

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")


def import_metrics_file(metrics_path: Path, **kwargs: Any) -> dict[str, Any]:
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    artifacts_dir = metrics_path.parent
    return record_backtest_run(payload=payload, artifacts_dir=artifacts_dir, **kwargs)
