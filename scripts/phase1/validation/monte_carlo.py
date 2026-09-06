"""Monte Carlo simulation on trade PnL sequences."""

from __future__ import annotations

import numpy as np

from scripts.phase1.common import INITIAL_BANKROLL, RANDOM_SEED
from scripts.phase1.metrics import _max_dd

DEFAULT_SIMS = 1000


def _equity_curve(pnls: list[float]) -> np.ndarray:
    return np.cumsum(pnls)


def run_monte_carlo(
    pnls: list[float],
    *,
    n_sims: int = DEFAULT_SIMS,
    seed: int = RANDOM_SEED,
    ruin_threshold: float | None = None,
) -> dict:
    if not pnls:
        return {
            "n_sims": 0,
            "n_trades": 0,
            "p5_dd": float("nan"),
            "p50_dd": float("nan"),
            "p95_dd": float("nan"),
            "p_profit": float("nan"),
            "p_ruin": float("nan"),
        }

    rng = np.random.default_rng(seed)
    ruin = ruin_threshold if ruin_threshold is not None else -INITIAL_BANKROLL * 0.5
    dds: list[float] = []
    final_pnl: list[float] = []
    ruined = 0

    arr = np.array(pnls, dtype=float)
    for _ in range(n_sims):
        sample = rng.choice(arr, size=len(arr), replace=True)
        eq = _equity_curve(sample.tolist())
        dds.append(_max_dd(sample.tolist()))
        final_pnl.append(float(eq[-1]))
        if float(eq.min()) <= ruin:
            ruined += 1

    return {
        "n_sims": n_sims,
        "n_trades": len(pnls),
        "p5_dd": float(np.percentile(dds, 5)),
        "p50_dd": float(np.percentile(dds, 50)),
        "p95_dd": float(np.percentile(dds, 95)),
        "p_profit": float(np.mean([1 if p > 0 else 0 for p in final_pnl])),
        "p_ruin": ruined / n_sims,
    }


def run_trade_shuffle(pnls: list[float], *, n_sims: int = DEFAULT_SIMS, seed: int = RANDOM_SEED) -> dict:
    if not pnls:
        return {"n_sims": 0, "p95_dd": float("nan"), "p_profit": float("nan")}

    rng = np.random.default_rng(seed)
    dds: list[float] = []
    final_pnl: list[float] = []
    arr = list(pnls)

    for _ in range(n_sims):
        sample = arr.copy()
        rng.shuffle(sample)
        dds.append(_max_dd(sample))
        final_pnl.append(float(sum(sample)))

    return {
        "n_sims": n_sims,
        "p95_dd": float(np.percentile(dds, 95)),
        "p_profit": float(np.mean([1 if p > 0 else 0 for p in final_pnl])),
    }
