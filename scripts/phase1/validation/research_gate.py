"""Research Gate evaluation (quality tier, distinct from Business Gate2)."""

from __future__ import annotations

import math

import numpy as np

from scripts.phase1.common import (
    RESEARCH_GATE_DD_MAX,
    RESEARCH_GATE_MC_DD_P95_MAX,
    RESEARCH_GATE_MC_RUIN_MAX,
    RESEARCH_GATE_PF_MIN,
    RESEARCH_GATE_WF_PASS_RATE,
)


def evaluate_research_gate(
    stats: dict,
    wf_result: dict,
    mc_result: dict,
    robustness: dict,
) -> dict:
    reasons: list[str] = []
    checks: dict[str, bool] = {}

    ev = stats.get("executed_ev") or stats.get("ev") or 0
    checks["ev_positive"] = ev > 0
    if not checks["ev_positive"]:
        reasons.append("executed EV <= 0")

    pf = stats.get("profit_factor")
    if pf is None or (isinstance(pf, float) and np.isnan(pf)):
        pf = 0
    checks["pf_min"] = bool(pf >= RESEARCH_GATE_PF_MIN or math.isinf(pf))
    if not checks["pf_min"]:
        reasons.append(f"PF {pf:.2f} < {RESEARCH_GATE_PF_MIN}")

    dd = stats.get("max_dd") or 0
    checks["dd_limit"] = dd <= RESEARCH_GATE_DD_MAX
    if not checks["dd_limit"]:
        reasons.append(f"maxDD ¥{dd:.0f} > ¥{RESEARCH_GATE_DD_MAX:.0f}")

    wf_rate = wf_result.get("pass_rate") or 0
    checks["wf_pass"] = wf_rate >= RESEARCH_GATE_WF_PASS_RATE
    if not checks["wf_pass"]:
        reasons.append(f"WF pass rate {wf_rate:.0%} < {RESEARCH_GATE_WF_PASS_RATE:.0%}")

    p95_dd = mc_result.get("p95_dd") or float("inf")
    checks["mc_dd"] = p95_dd <= RESEARCH_GATE_MC_DD_P95_MAX
    if not checks["mc_dd"]:
        reasons.append(f"MC p95 DD ¥{p95_dd:.0f} > ¥{RESEARCH_GATE_MC_DD_P95_MAX:.0f}")

    p_ruin = mc_result.get("p_ruin")
    if p_ruin is None:
        p_ruin = 1.0
    checks["mc_ruin"] = p_ruin <= RESEARCH_GATE_MC_RUIN_MAX
    if not checks["mc_ruin"]:
        reasons.append(f"MC ruin prob {p_ruin:.1%} > {RESEARCH_GATE_MC_RUIN_MAX:.1%}")

    checks["robustness"] = bool(robustness.get("pass"))
    if not checks["robustness"]:
        reasons.append("robustness stress fail (PF < 1 under +20% fee/slip)")

    passed = all(checks.values())
    return {
        "pass": passed,
        "checks": checks,
        "reasons": reasons,
        "verdict": "pass" if passed else "fail",
    }
