# DB-29 / db_1h_stop_bottom_v1 — Set B

- **Run ID:** `20260823-031`
- **記録日時:** 2026-08-23T02:01:24Z
- **ステータス:** `pass`
- **ゲート:** PASS

## 1. 仮説

**名称:** 1H+第2底損切

**一言:** Formal eval PASS

**狙う歪み:** E1

## 2. 売買ロジック

- **eval_version:** eval_v1.1
- **set:** B

## 3. 検証条件

| 項目 | 値 |
|------|-----|
| 評価期間 | 2024-01-01 → 2024-12-31 |
| データ | binance_vision |
| 合成データ | False |
| 15m本数 | 35136 |
| 設定 | `configs/eval_v1.yaml` |
| Git | `6011e9e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 105 |
| 1トレード平均損益 | 0.01731085201757844 |
| 総リターン | -0.9239056879453811% |
| 月次換算（近似） | -0.07716392021950291% |
| 最大DD | 6.587222000426518% |
| 勝率 | 33.33333333333333% |
| 最終資産 | 297.22828293616385 |

**ゲート不合格理由:** —

## 5. 知見

実データ(binance_vision) Set B。costs=eval_v1 lock。 ゲート合格。

**残す:**
- 実データ + 固定コストでの判定

**捨てる:**
- 合成 smoke を合否に使うこと

## 6. 次アクション

- Set C holdout
- demo 設計

## 7. 成果物

- `artifacts/evals/20260823T020123Z_setB_db_1h_stop_bottom_v1/`
- `artifacts/evals/20260823T020123Z_setB_db_1h_stop_bottom_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
