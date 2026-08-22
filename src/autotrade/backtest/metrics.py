from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from autotrade.backtest.engine import BacktestResult, Trade


@dataclass
class Metrics:
    trades: int
    total_return_pct: float
    monthly_return_pct_approx: float
    avg_trade_pnl: float
    expectancy_positive: bool
    win_rate_pct: float
    max_drawdown_pct: float
    payoff_ratio: float | None
    total_fees: float
    long_trades: int
    short_trades: int
    gate_min_trades_ok: bool
    gate_expectancy_ok: bool
    gate_drawdown_ok: bool
    gate_pass: bool


def max_drawdown_pct(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = (equity - peak) / peak * 100.0
    return float(dd.min())  # negative number; report absolute below


def compute_metrics(
    result: BacktestResult,
    *,
    min_trades: int,
    max_drawdown_pct_limit: float,
) -> Metrics:
    trades = result.trades
    n = len(trades)
    total_ret = (result.final_equity / result.initial_equity - 1.0) * 100.0

    if result.equity_curve.index.size >= 2:
        days = (result.equity_curve.index[-1] - result.equity_curve.index[0]).total_seconds() / 86400.0
        months = max(days / 30.4375, 1e-9)
        monthly = ((result.final_equity / result.initial_equity) ** (1 / months) - 1.0) * 100.0
    else:
        monthly = 0.0

    pnls = [t.pnl for t in trades]
    avg = sum(pnls) / n if n else 0.0
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    win_rate = len(wins) / n * 100.0 if n else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    payoff = (avg_win / avg_loss) if avg_loss > 0 else None
    fees = sum(t.fee for t in trades)
    dd = abs(max_drawdown_pct(result.equity_curve))

    gate_trades = n >= min_trades
    gate_exp = avg > 0
    gate_dd = dd <= max_drawdown_pct_limit

    return Metrics(
        trades=n,
        total_return_pct=total_ret,
        monthly_return_pct_approx=monthly,
        avg_trade_pnl=avg,
        expectancy_positive=gate_exp,
        win_rate_pct=win_rate,
        max_drawdown_pct=dd,
        payoff_ratio=payoff,
        total_fees=fees,
        long_trades=sum(1 for t in trades if t.side == "long"),
        short_trades=sum(1 for t in trades if t.side == "short"),
        gate_min_trades_ok=gate_trades,
        gate_expectancy_ok=gate_exp,
        gate_drawdown_ok=gate_dd,
        gate_pass=gate_trades and gate_exp and gate_dd,
    )


def metrics_to_dict(m: Metrics) -> dict:
    return asdict(m)


def monthly_returns(trades: list[Trade], initial_equity: float) -> pd.Series:
    if not trades:
        return pd.Series(dtype=float)
    df = pd.DataFrame(
        {"exit_time": [t.exit_time for t in trades], "pnl": [t.pnl for t in trades]}
    )
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True)
    df = df.set_index("exit_time").sort_index()
    monthly_pnl = df["pnl"].resample("ME").sum()
    return monthly_pnl / initial_equity * 100.0
