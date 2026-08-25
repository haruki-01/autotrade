# Formal Eval Reference

## Locked numbers (`configs/eval_v1.yaml`)

| Item | Value |
|------|-------|
| Symbol | BTCUSDT linear (Bybit target) |
| Initial equity | 10,000 USDT |
| Leverage | 3.0 |
| Risk / trade | 1.0% |
| Fee / side | 0.00055 (5.5 bps) |
| Slippage / side | 0.0002 (2 bps) |
| Set A | 2023-01-01 → 2023-12-31 |
| Set B (primary) | 2024-01-01 → 2024-12-31 |
| Set C (holdout) | 2025-01-01 → 2026-08-22 |
| Min trades | 100 |
| Max DD | 20% |

## データポリシー（混線防止）

- 実データ Bybit: `BTCUSDT_linear_*`
- 実データ Vision: `BTCUSDT_binance_spot_*`
- 合成: `BTCUSDT_synthetic_*`（合否禁止。旧 `linear` への上書きは廃止済み）

`eval-prepare` は Bybit を API プローブしてから使う。不通なら Vision のみ（汚染された linear キャッシュは読まない）。

## CLI

```bash
# Prepare / refresh lock
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --force   # re-download

# Evaluate
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id cost_gate_v1
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id mtf_ema_pullback_v1 --set C
```

## Outputs

| Path | Content |
|------|---------|
| `eval/locks/eval_v1.lock.yaml` | Environment fingerprint |
| `eval/reports/<stamp>_<logic>_setB.md` | Human report |
| `artifacts/evals/<stamp>_.../` | metrics.json, trades.csv, equity |
| `docs/research/` | Registry + entry |
| `docs/workstreams/<id>/LATEST.md` | Per-logic latest |

## Known logic IDs

- `mtf_ema_pullback_v1` (H01)
- `cost_gate_v1` (L-COST)
- `vol_scaled_trend_v1` (L-MOM-VOL)
- `donchian_20_10_v1` (L-BREAK)
- `donchian_20_10_long_only` (H21)
