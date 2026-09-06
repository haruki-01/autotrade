"""Extended risk metrics for hybrid validation."""

from __future__ import annotations

import numpy as np

from scripts.phase1.common import Trade, months_in_df
from scripts.phase1.metrics import _max_dd, summarize_trades


def profit_factor(pnls: list[float]) -> float:
    wins = sum(p for p in pnls if p > 0)
    losses = abs(sum(p for p in pnls if p < 0))
    if losses == 0:
        return float("inf") if wins > 0 else float("nan")
    return wins / losses


def sharpe_trades(pnls: list[float], trades_per_year: float) -> float:
    if len(pnls) < 2 or trades_per_year <= 0:
        return float("nan")
    std = float(np.std(pnls, ddof=1))
    if std == 0:
        return float("nan")
    return float(np.mean(pnls) / std * np.sqrt(trades_per_year))


def sortino_trades(pnls: list[float], trades_per_year: float) -> float:
    if len(pnls) < 2 or trades_per_year <= 0:
        return float("nan")
    downside = [p for p in pnls if p < 0]
    if not downside:
        return float("inf")
    dd_std = float(np.std(downside, ddof=1))
    if dd_std == 0:
        return float("nan")
    return float(np.mean(pnls) / dd_std * np.sqrt(trades_per_year))


def summarize_excursions(trades: list[Trade]) -> dict:
    filled = [t for t in trades if t.filled]
    if not filled:
        return {
            "avg_mfe_pct": float("nan"),
            "avg_mae_pct": float("nan"),
            "mfe_mae_ratio": float("nan"),
            "edge_efficiency": float("nan"),
        }
    mfe = [t.mfe_pct for t in filled]
    mae = [t.mae_pct for t in filled]
    avg_mfe = float(np.mean(mfe))
    avg_mae = float(np.mean(mae))
    ratio = avg_mfe / avg_mae if avg_mae > 0 else float("nan")
    wins = [t for t in filled if t.executed_pnl > 0]
    eff = float(np.mean([t.executed_ret / t.mfe_pct for t in wins if t.mfe_pct > 0])) if wins else float("nan")
    return {
        "avg_mfe_pct": avg_mfe,
        "avg_mae_pct": avg_mae,
        "mfe_mae_ratio": ratio,
        "edge_efficiency": eff,
    }


def extended_summarize(trades: list[Trade], df, pnl_attr: str = "executed_pnl") -> dict:
    base = summarize_trades(trades, df, pnl_attr)
    pnls = [getattr(t, pnl_attr) for t in trades if t.filled]
    months = months_in_df(df)
    trades_per_year = (len(pnls) / months) * 12 if months > 0 else 0.0
    excursions = summarize_excursions(trades)
    return {
        **base,
        "profit_factor": profit_factor(pnls) if pnls else float("nan"),
        "sharpe": sharpe_trades(pnls, trades_per_year) if pnls else float("nan"),
        "sortino": sortino_trades(pnls, trades_per_year) if pnls else float("nan"),
        **excursions,
    }
