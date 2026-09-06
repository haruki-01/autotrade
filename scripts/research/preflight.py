"""Preflight checks before Phase1/L1/L3 batch execution."""

from __future__ import annotations

import subprocess
from typing import Any, Callable

SPEC_VERSION = "0.2"


def batch_metadata() -> dict[str, str]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    return {"spec_version": SPEC_VERSION, "git_commit": commit}


def run_preflight(checks: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = True
    for check in checks:
        ok = bool(check.get("ok", False))
        level = check.get("level", "error")
        if not ok and level == "error":
            passed = False
        results.append(
            {
                "name": check.get("name", "unnamed"),
                "ok": ok,
                "level": level,
                "detail": check.get("detail", ""),
            }
        )
    return {"passed": passed, "checks": results}


def check_signal_count(
    label: str,
    count: int,
    min_count: int = 10,
    expected_monthly: float | None = None,
    monthly_tolerance: float = 0.5,
) -> dict[str, Any]:
    ok = count >= min_count
    detail = f"{label}: count={count} (min={min_count})"
    if expected_monthly is not None:
        detail += f", expected_monthly≈{expected_monthly:.1f}"
    return {"name": f"signal_count_{label}", "ok": ok, "level": "error", "detail": detail}


def check_sign_consistency(
    label: str,
    phase0_mean: float | None,
    phase1_theoretical_ev: float | None,
) -> dict[str, Any]:
    if phase0_mean is None or phase1_theoretical_ev is None:
        return {
            "name": f"sign_parity_{label}",
            "ok": True,
            "level": "warn",
            "detail": "skipped (missing baseline)",
        }
    if np_isnan(phase0_mean) or np_isnan(phase1_theoretical_ev):
        return {
            "name": f"sign_parity_{label}",
            "ok": True,
            "level": "warn",
            "detail": "skipped (nan values)",
        }
    same_sign = (phase0_mean >= 0) == (phase1_theoretical_ev >= 0)
    return {
        "name": f"sign_parity_{label}",
        "ok": same_sign,
        "level": "warn" if not same_sign else "info",
        "detail": f"P0 mean={phase0_mean:.4f}, P1 theory EV={phase1_theoretical_ev:.4f}",
    }


def np_isnan(x: float) -> bool:
    import math

    return math.isnan(x)


def run_module_preflight(mod, df, *, phase0_baseline: dict | None = None) -> dict[str, Any]:
    """Call module.preflight(df) if defined; else empty pass."""
    fn: Callable | None = getattr(mod, "preflight", None)
    if fn is None:
        return run_preflight([{"name": "preflight", "ok": True, "level": "info", "detail": "no checks defined"}])
    checks = fn(df, phase0_baseline=phase0_baseline)
    if isinstance(checks, dict) and "passed" in checks:
        return checks
    return run_preflight(checks if isinstance(checks, list) else [])
