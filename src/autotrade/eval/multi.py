"""Multi-symbol evaluation lock and loading.

The single-symbol lock in :mod:`autotrade.eval` stays exactly as it is so the
eval_v1 results remain reproducible. This module adds a parallel lock whose
datasets are keyed by set and then by symbol.

Why a basket at all: at daily-ATR stop distances one symbol produces roughly
20-40 trades a year, which cannot reach ``min_trades`` on a one-year set. The
choice is to weaken the gate or to gather the trades elsewhere. A fixed,
pre-declared basket does the latter, and doubles as a cross-symbol replication
test -- a real mechanism should not care which coin it runs on.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from autotrade.data.binance_derivatives import (
    KINDS as DERIV_KINDS,
    align_to_15m,
    cache_path as deriv_cache_path,
    ensure_derivative,
)
from autotrade.data.binance_vision import BinanceVisionClient, ensure_binance_data
from autotrade.data.bybit import load_ohlcv
from autotrade.eval import _cache_path, _set_bounds, _sha256_file, _git_head, load_eval_config

MULTI_LOCK_PATH = Path("eval/locks/eval_v2.lock.yaml")


def config_symbols(raw: dict[str, Any], fallback: str) -> list[str]:
    return list(raw.get("symbols") or [fallback])


def _ohlcv_files(cfg, symbol: str, set_name: str, cache_dir: Path, force: bool) -> dict[str, str]:
    start, end = _set_bounds(cfg, set_name)
    vision = BinanceVisionClient()
    hashes: dict[str, str] = {}
    for interval in ("1d", "4h", "15m"):
        ensure_binance_data(
            vision,
            symbol=symbol,
            interval=interval,
            start=start,
            end=end,
            cache_dir=cache_dir,
            force=force,
        )
        path = _cache_path(
            cache_dir,
            source="binance_vision",
            symbol=symbol,
            category=cfg.category,
            interval=interval,
            start=start,
            end=end,
        )
        hashes[str(path.as_posix())] = _sha256_file(path)
    return hashes


def _deriv_files(cfg, symbol: str, set_name: str, cache_dir: Path, force: bool) -> dict[str, str]:
    start, end = _set_bounds(cfg, set_name)
    hashes: dict[str, str] = {}
    for kind in DERIV_KINDS:
        ensure_derivative(
            symbol=symbol, kind=kind, start=start, end=end, cache_dir=cache_dir, force=force
        )
        path = deriv_cache_path(cache_dir, symbol, kind, start, end)
        hashes[str(path.as_posix())] = _sha256_file(path)
    return hashes


def prepare_multi_lock(
    config_path: str | Path,
    *,
    sets: list[str] | None = None,
    symbols: list[str] | None = None,
    force: bool = False,
    with_derivatives: bool = True,
    lock_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    cfg, policy, raw = load_eval_config(config_path)
    sets = sets or list(raw.get("required_sets") or ["A", "B", "C"])
    symbols = symbols or config_symbols(raw, cfg.symbol)
    cache_dir = cache_dir or Path("data/cache")
    lock_path = lock_path or MULTI_LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    datasets: dict[str, Any] = {}
    for set_name in sets:
        if set_name not in cfg.sets:
            continue
        start, end = _set_bounds(cfg, set_name)
        per_symbol: dict[str, Any] = {}
        for symbol in symbols:
            entry = {
                "fetch_window": {"start": start, "end": end},
                "data_source": "binance_vision",
                "files": _ohlcv_files(cfg, symbol, set_name, cache_dir, force),
            }
            if with_derivatives:
                entry["derivatives"] = _deriv_files(cfg, symbol, set_name, cache_dir, force)
            per_symbol[symbol] = entry
        datasets[set_name] = {
            "eval_window": {"start": cfg.sets[set_name].start, "end": cfg.sets[set_name].end},
            "symbols": per_symbol,
        }

    lock = {
        "schema_version": 1,
        "eval_version": policy.eval_version,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_head(),
        "config_path": str(Path(config_path).as_posix()),
        "config_sha256": _sha256_file(Path(config_path)),
        "forbid_synthetic": True,
        "symbols": symbols,
        "costs": {
            "fee_rate_per_side": cfg.fee_rate_per_side,
            "slippage_pct_per_side": cfg.slippage_pct_per_side,
        },
        "sizing": {
            "mode": cfg.sizing_mode,
            "margin_per_trade": cfg.margin_per_trade,
            "risk_per_trade_usdt": cfg.risk_per_trade_usdt,
            "leverage": cfg.leverage,
            "initial_equity": cfg.initial_equity,
        },
        "gates": {
            "min_trades": cfg.min_trades,
            "max_drawdown_pct": cfg.max_drawdown_pct,
            "min_trades_scope": "portfolio total across symbols, per set",
        },
        "datasets": datasets,
        "notes": (
            "Multi-symbol formal eval. Trades from every symbol merge into one equity "
            "curve; fixed_margin sizing makes the per-symbol runs independent."
        ),
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(lock, f, allow_unicode=True, sort_keys=False)
    return lock


def validate_multi_lock(lock: dict[str, Any], set_name: str) -> list[str]:
    errors: list[str] = []
    ds = (lock.get("datasets") or {}).get(set_name)
    if not ds:
        return [f"set {set_name} missing from lock — run prepare"]
    for symbol, entry in (ds.get("symbols") or {}).items():
        for group in ("files", "derivatives"):
            for path_str, expected in (entry.get(group) or {}).items():
                path = Path(path_str)
                if not path.exists():
                    errors.append(f"{symbol}: missing {path_str}")
                    continue
                if _sha256_file(path) != expected:
                    errors.append(f"{symbol}: hash mismatch {path_str}")
    return errors


def load_multi_frames(
    lock: dict[str, Any], set_name: str, symbol: str
) -> dict[str, pd.DataFrame]:
    entry = lock["datasets"][set_name]["symbols"][symbol]
    frames: dict[str, pd.DataFrame] = {}
    for path_str in entry["files"]:
        name = Path(path_str).name
        if "_15m_" in name:
            frames["15m"] = load_ohlcv(Path(path_str))
        elif "_4h_" in name:
            frames["4h"] = load_ohlcv(Path(path_str))
        elif "_1d_" in name:
            frames["1d"] = load_ohlcv(Path(path_str))
    missing = [k for k in ("1d", "4h", "15m") if k not in frames]
    if missing:
        raise RuntimeError(f"{symbol} set {set_name}: missing frames {missing}")
    return frames


def load_multi_derivatives(
    lock: dict[str, Any], set_name: str, symbol: str, m15_index: pd.DatetimeIndex
) -> pd.DataFrame:
    entry = lock["datasets"][set_name]["symbols"][symbol]
    files = entry.get("derivatives") or {}
    if not files:
        raise RuntimeError(f"{symbol} set {set_name}: lock has no derivative files")
    loaded: dict[str, pd.DataFrame] = {}
    for path_str in files:
        path = Path(path_str)
        kind = next((k for k in DERIV_KINDS if f"_{k}_" in path.name), None)
        if kind is None:
            continue
        df = pd.read_csv(path, parse_dates=["timestamp"])
        loaded[kind] = df.set_index("timestamp").sort_index()
    missing = [k for k in DERIV_KINDS if k not in loaded]
    if missing:
        raise RuntimeError(f"{symbol} set {set_name}: derivative lock incomplete {missing}")
    return align_to_15m(
        m15_index,
        metrics=loaded["metrics"],
        funding=loaded["funding"],
        premium=loaded["premium"],
        perp=loaded["perp15m"],
    )
