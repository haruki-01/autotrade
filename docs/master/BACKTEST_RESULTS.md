# Backtest run log

## 2026-08-22 — Set B (primary gate)

| Item | Value |
|------|--------|
| Eval window | 2024-01-01 → 2024-12-31 |
| Data source | **Binance Vision** BTCUSDT spot (Bybit blocked in Cloud; geo 403) |
| Bars (15m) | 35,136 |
| Strategy | Hypothesis v1 (1D/4H/15m EMA trend pullback) |
| Leverage | 3x |
| Costs | fee 5.5bps/side + slip 2bps/side |

### Metrics

| Metric | Value | Gate |
|--------|-------|------|
| Trades | 594 | ≥100 ✅ |
| Avg trade PnL | **-3.10** USDT | >0 ❌ |
| Total return | **-43.3%** | — |
| Approx monthly | **-4.6%** | — |
| Max drawdown | **49.4%** | ≤20% ❌ |
| Win rate | 40.2% | (reference) |
| Final equity | 5,672 / 10,000 | — |

**GATE: FAIL**

Artifacts: `artifacts/backtests/20260822T050037Z_setB/`

### Interpretation

- Pipeline works on **real** OHLCV (not synthetic).
- Current v1 rules are **not** edge-positive on 2024 after costs.
- Do **not** go to demo/live with this parameter set.
- Next: change **one** entry/exit rule at a time (per IMPLEMENTATION_PLAN), re-run B, avoid large grid search.
- Before any live decision, re-fetch with **Bybit** on a local machine (same code path).

### Caveat

Binance Vision spot ≠ Bybit linear exactly (funding, microstructure). Good enough to reject a clearly losing rule set; not enough to green-light live.

## 2026-08-25 — SH-01 EV+DD campaign

Formal, real data, `eval_v3_btc`. Monthly 50 is not a gate.

| Item | `sh01n_center` |
|------|----------------|
| Sets A/B/C EV | +1.951 / +0.528 / +0.456 |
| DD | 2.8% / 5.3% / 7.6% |
| Pooled | n=164, EV +0.989, t=+2.57 |
| Gate | EV+DD **PASS**; per-set n **HOLD** |
| Set C vs BTC hold (ret/DD) | 1.14 vs 1.51 (lose) |

Report: `eval/reports/20260825-slow-evdd.md`

## 2026-08-25 — SH-01 rest filters (論点B)

One-point SMA / long-only on `sh01n_center`. Formal, same lock.

| Item | `sh01n_regime_100d` |
|------|---------------------|
| Pooled | n=133, EV +1.306, t=+3.01 |
| Set C ret/DD vs BTC hold | **3.44 vs 1.51** |
| 3-period ret/DD vs hold | win / win / win（50d も同じ） |
| Control `regime_against` | Set C EV −0.779 **FAIL** |

Report: `eval/reports/20260825-slow-rest.md`

