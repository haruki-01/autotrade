"""Formal evaluation: real-data only, locked config & costs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from autotrade.config import BacktestConfig, load_config
from autotrade.data.binance_vision import BinanceVisionClient, ensure_binance_data
from autotrade.data.bybit import BybitPublicClient, ensure_data, load_ohlcv
from autotrade.backtest.engine import run_backtest, trades_to_frame
from autotrade.backtest.metrics import compute_metrics, metrics_to_dict, monthly_returns
from autotrade.strategy.registry import LOGIC_META, prepare_strategy
from autotrade.research.log import record_backtest_run

LOCK_PATH = Path("eval/locks/eval_v1.lock.yaml")
REPORTS_DIR = Path("eval/reports")
ARTIFACTS_ROOT = Path("artifacts/evals")


@dataclass
class EvalPolicy:
    eval_version: str
    forbid_synthetic: bool
    preferred_data_source: str
    allowed_data_sources: list[str]
    primary_gate_set: str
    holdout_set: str


def load_eval_config(path: str | Path) -> tuple[BacktestConfig, EvalPolicy, dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    cfg = BacktestConfig.from_dict(raw)
    policy = EvalPolicy(
        eval_version=str(raw.get("eval_version", "unknown")),
        forbid_synthetic=bool(raw.get("forbid_synthetic", True)),
        preferred_data_source=str(raw.get("preferred_data_source", "bybit")),
        allowed_data_sources=list(raw.get("allowed_data_sources") or ["bybit"]),
        primary_gate_set=str(raw.get("primary_gate_set", "B")),
        holdout_set=str(raw.get("holdout_set", "C")),
    )
    return cfg, policy, raw


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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _set_bounds(cfg: BacktestConfig, set_name: str) -> tuple[str, str]:
    warm_days = max(cfg.daily_ema * 2, 220)
    start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC") - pd.Timedelta(days=warm_days)
    end = cfg.sets[set_name].end
    return start.strftime("%Y-%m-%d"), end


def _cache_path(
    cache_dir: Path,
    *,
    source: str,
    symbol: str,
    category: str,
    interval: str,
    start: str,
    end: str,
) -> Path:
    if source == "binance_vision":
        return cache_dir / f"{symbol}_binance_spot_{interval}_{start}_{end}.csv"
    return cache_dir / f"{symbol}_{category}_{interval}_{start}_{end}.csv"


def _probe_bybit(cfg: BacktestConfig) -> bool:
    client = BybitPublicClient(base_url=cfg.base_url)
    try:
        start_ms = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
        end_ms = int(pd.Timestamp("2024-01-03", tz="UTC").timestamp() * 1000)
        df = client.fetch_klines(
            cfg.symbol, "1d", category=cfg.category, start_ms=start_ms, end_ms=end_ms, limit=5
        )
        return len(df) > 0
    except Exception:  # noqa: BLE001
        return False


def fetch_real_frames(
    cfg: BacktestConfig,
    policy: EvalPolicy,
    set_name: str,
    *,
    force: bool = False,
    cache_dir: Path | None = None,
) -> tuple[dict[str, pd.DataFrame], str, dict[str, str]]:
    """Fetch real OHLCV only. Never reads synthetic caches."""
    cache_dir = cache_dir or Path("data/cache")
    start, end = _set_bounds(cfg, set_name)
    file_hashes: dict[str, str] = {}

    bybit_ok = "bybit" in policy.allowed_data_sources and _probe_bybit(cfg)
    if bybit_ok:
        client = BybitPublicClient(base_url=cfg.base_url)
        frames: dict[str, pd.DataFrame] = {}
        for interval in ("1d", "4h", "15m"):
            frames[interval] = ensure_data(
                client,
                symbol=cfg.symbol,
                category=cfg.category,
                interval=interval,
                start=start,
                end=end,
                cache_dir=cache_dir,
                force=force,
            )
            path = _cache_path(
                cache_dir,
                source="bybit",
                symbol=cfg.symbol,
                category=cfg.category,
                interval=interval,
                start=start,
                end=end,
            )
            file_hashes[str(path.as_posix())] = _sha256_file(path)
        return frames, "bybit", file_hashes

    if "binance_vision" not in policy.allowed_data_sources:
        raise RuntimeError(
            "Bybit unreachable and binance_vision not allowed. "
            "Formal eval requires real market data."
        )

    vision = BinanceVisionClient()
    frames = {}
    for interval in ("1d", "4h", "15m"):
        frames[interval] = ensure_binance_data(
            vision,
            symbol=cfg.symbol,
            interval=interval,
            start=start,
            end=end,
            cache_dir=cache_dir,
            force=force,
        )
        path = _cache_path(
            cache_dir,
            source="binance_vision",
            symbol=cfg.symbol,
            category=cfg.category,
            interval=interval,
            start=start,
            end=end,
        )
        file_hashes[str(path.as_posix())] = _sha256_file(path)
    return frames, "binance_vision", file_hashes


def prepare_eval_lock(
    config_path: str | Path,
    *,
    sets: list[str] | None = None,
    force: bool = False,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    cfg, policy, raw = load_eval_config(config_path)
    sets = sets or ["A", "B", "C"]
    lock_path = lock_path or LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    datasets: dict[str, Any] = {}
    for name in sets:
        if name not in cfg.sets:
            continue
        frames, source, hashes = fetch_real_frames(cfg, policy, name, force=force)
        start, end = _set_bounds(cfg, name)
        datasets[name] = {
            "eval_window": {"start": cfg.sets[name].start, "end": cfg.sets[name].end},
            "fetch_window": {"start": start, "end": end},
            "data_source": source,
            "bars": {k: len(v) for k, v in frames.items()},
            "files": hashes,
        }

    lock = {
        "schema_version": 1,
        "eval_version": policy.eval_version,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_head(),
        "config_path": str(Path(config_path).as_posix()),
        "config_sha256": _sha256_file(Path(config_path)),
        "forbid_synthetic": True,
        "costs": {
            "fee_rate_per_side": cfg.fee_rate_per_side,
            "slippage_pct_per_side": cfg.slippage_pct_per_side,
            "initial_equity": cfg.initial_equity,
            "leverage": cfg.leverage,
            "risk_per_trade_pct": cfg.risk_per_trade_pct,
            "sizing_mode": cfg.sizing_mode,
            "margin_per_trade": cfg.margin_per_trade,
            "risk_per_trade_usdt": cfg.risk_per_trade_usdt,
        },
        "gates": {
            "min_trades": cfg.min_trades,
            "max_drawdown_pct": cfg.max_drawdown_pct,
            "primary_gate_set": policy.primary_gate_set,
            "holdout_set": policy.holdout_set,
        },
        "datasets": datasets,
        "notes": (
            "Formal eval only. Re-run eval-prepare after changing config or refreshing data. "
            "If data_source is binance_vision, re-confirm on Bybit before any live decision."
        ),
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(lock, f, allow_unicode=True, sort_keys=False)
    return lock


def validate_lock(
    lock: dict[str, Any],
    *,
    config_path: Path,
    set_name: str,
) -> list[str]:
    errors: list[str] = []
    if not lock.get("forbid_synthetic", True):
        errors.append("lock.forbid_synthetic must be true")
    if _sha256_file(config_path) != lock.get("config_sha256"):
        errors.append(
            f"config hash mismatch: {config_path} changed since lock. Re-run eval-prepare."
        )
    ds = (lock.get("datasets") or {}).get(set_name)
    if not ds:
        errors.append(f"set {set_name} missing from lock — run eval-prepare")
        return errors
    source = ds.get("data_source")
    if source == "synthetic":
        errors.append("synthetic data is forbidden for formal eval")
    if source not in ("bybit", "binance_vision"):
        errors.append(f"unsupported data_source in lock: {source}")
    for path_str, expected in (ds.get("files") or {}).items():
        path = Path(path_str)
        if "_synthetic_" in path.name:
            errors.append(f"synthetic cache path in lock: {path_str}")
            continue
        if not path.exists():
            errors.append(f"missing data file: {path_str}")
            continue
        actual = _sha256_file(path)
        if actual != expected:
            errors.append(f"hash mismatch for {path_str}: re-fetch or update lock")
    return errors


def load_locked_frames(lock: dict[str, Any], set_name: str) -> tuple[dict[str, pd.DataFrame], str]:
    ds = lock["datasets"][set_name]
    source = ds["data_source"]
    frames: dict[str, pd.DataFrame] = {}
    # Map interval from filename
    for path_str in ds["files"]:
        path = Path(path_str)
        name = path.name
        if "_15m_" in name:
            frames["15m"] = load_ohlcv(path)
        elif "_4h_" in name:
            frames["4h"] = load_ohlcv(path)
        elif "_1d_" in name:
            frames["1d"] = load_ohlcv(path)
    missing = [k for k in ("1d", "4h", "15m") if k not in frames]
    if missing:
        raise RuntimeError(f"lock files incomplete for set {set_name}: missing {missing}")
    return frames, source


def run_formal_eval(
    *,
    config_path: str | Path,
    logic_id: str,
    set_name: str | None = None,
    lock_path: Path | None = None,
    write_research_log: bool = True,
) -> dict[str, Any]:
    cfg, policy, _raw = load_eval_config(config_path)
    set_name = set_name or policy.primary_gate_set
    lock_path = lock_path or LOCK_PATH
    if not lock_path.exists():
        raise RuntimeError(f"Missing lock {lock_path}. Run: autotrade eval-prepare")

    with open(lock_path, encoding="utf-8") as f:
        lock = yaml.safe_load(f)

    errors = validate_lock(lock, config_path=Path(config_path), set_name=set_name)
    if errors:
        raise RuntimeError("Eval environment invalid:\n- " + "\n- ".join(errors))

    if logic_id not in LOGIC_META:
        raise ValueError(f"Unknown logic_id: {logic_id}")

    frames, source = load_locked_frames(lock, set_name)
    if source == "synthetic" or (policy.forbid_synthetic and source not in policy.allowed_data_sources):
        raise RuntimeError(f"Refusing eval on data_source={source}")

    prepared = prepare_strategy(logic_id, frames["1d"], frames["4h"], frames["15m"], cfg=cfg)
    set_start = pd.Timestamp(cfg.sets[set_name].start, tz="UTC")
    set_end = pd.Timestamp(cfg.sets[set_name].end, tz="UTC") + pd.Timedelta(days=1)
    prepared = prepared[(prepared.index >= set_start) & (prepared.index < set_end)]
    if prepared.empty:
        raise RuntimeError("No bars in evaluation window")

    result = run_backtest(
        prepared,
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
    metrics = compute_metrics(
        result,
        min_trades=cfg.min_trades,
        max_drawdown_pct_limit=cfg.max_drawdown_pct,
    )

    meta = LOGIC_META[logic_id]
    hypothesis_id = meta["hypothesis_id"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ARTIFACTS_ROOT / f"{stamp}_set{set_name}_{logic_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    trades_df = trades_to_frame(result.trades)
    trades_df.to_csv(out_dir / "trades.csv", index=False)
    result.equity_curve.to_csv(out_dir / "equity_curve.csv", header=True)
    monthly_returns(result.trades, cfg.initial_equity).to_csv(
        out_dir / "monthly_returns_pct.csv", header=["monthly_return_pct"]
    )

    payload = {
        "mode": "formal_eval",
        "eval_version": policy.eval_version,
        "set": set_name,
        "config": str(Path(config_path).as_posix()),
        "lock_path": str(lock_path.as_posix()),
        "logic_id": logic_id,
        "hypothesis_id": hypothesis_id,
        "eval_start": cfg.sets[set_name].start,
        "eval_end": cfg.sets[set_name].end,
        "bars": len(prepared),
        "synthetic": False,
        "data_source": source,
        "costs": lock.get("costs"),
        "git_commit": _git_head(),
        "metrics": metrics_to_dict(metrics),
        "final_equity": result.final_equity,
        "gate_pass": bool(metrics.gate_pass),
    }
    (out_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "env_lock_snapshot.yaml").write_text(
        yaml.safe_dump(
            {
                "eval_version": lock.get("eval_version"),
                "config_sha256": lock.get("config_sha256"),
                "costs": lock.get("costs"),
                "dataset": lock["datasets"][set_name],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    if write_research_log:
        learnings = {
            "one_liner": (
                "Formal eval PASS" if metrics.gate_pass else "Formal eval FAIL"
            ),
            "summary": (
                f"実データ({source}) Set {set_name}。costs=eval_v1 lock。"
                + (" ゲート合格。" if metrics.gate_pass else " ゲート不合格。")
            ),
            "keep": ["実データ + 固定コストでの判定"],
            "discard": ["合成 smoke を合否に使うこと"],
        }
        record_backtest_run(
            payload=payload,
            artifacts_dir=out_dir,
            hypothesis_id=hypothesis_id,
            logic_id=logic_id,
            hypothesis_name=meta["name"],
            distortion_ids=list(meta.get("distortion_ids") or []),
            logic_summary={"eval_version": policy.eval_version, "set": set_name},
            learnings=learnings,
            next_actions=(
                [f"Set {policy.holdout_set} holdout", "demo 設計"]
                if metrics.gate_pass
                else ["敗因を workstream notes に1点整理", "ルールを1点だけ変更して再 eval"]
            ),
            notes=f"formal_eval lock={lock_path}",
        )

    # Human-readable report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{stamp}_{logic_id}_set{set_name}.md"
    report_path.write_text(
        _format_report(payload, out_dir),
        encoding="utf-8",
    )
    payload["report_path"] = str(report_path.as_posix())
    payload["artifacts_dir"] = str(out_dir.as_posix())
    return payload


def _format_report(payload: dict[str, Any], out_dir: Path) -> str:
    m = payload["metrics"]
    gate = "PASS" if payload.get("gate_pass") else "FAIL"
    return "\n".join(
        [
            f"# Formal Eval — {payload['hypothesis_id']} / {payload['logic_id']}",
            "",
            f"- **Gate:** `{gate}`",
            f"- **Set:** {payload['set']}",
            f"- **Data:** {payload['data_source']} (synthetic forbidden)",
            f"- **Eval version:** {payload['eval_version']}",
            f"- **Costs:** fee={payload['costs']['fee_rate_per_side']} slip={payload['costs']['slippage_pct_per_side']} lev={payload['costs']['leverage']}",
            f"- **Git:** {payload.get('git_commit')}",
            f"- **Artifacts:** `{out_dir.as_posix()}`",
            "",
            "## Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Trades | {m.get('trades')} |",
            f"| Avg trade PnL | {m.get('avg_trade_pnl')} |",
            f"| Total return % | {m.get('total_return_pct')} |",
            f"| Max DD % | {m.get('max_drawdown_pct')} |",
            f"| Win rate % | {m.get('win_rate_pct')} |",
            f"| Fees | {m.get('total_fees')} |",
            "",
            "## Gate checks",
            "",
            f"- expectancy > 0: {m.get('gate_expectancy_ok')}",
            f"- min trades: {m.get('gate_min_trades_ok')}",
            f"- DD limit: {m.get('gate_drawdown_ok')}",
            "",
        ]
    )
