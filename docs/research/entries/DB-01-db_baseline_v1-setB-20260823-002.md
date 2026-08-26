# DB-01 / db_baseline_v1 — Set B

- **Run ID:** `20260823-002`
- **記録日時:** 2026-08-23T01:04:25Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** DB基準: 4H・終値突破・陽線反発

**一言:** Formal eval FAIL

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
| Git | `933022e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 34 |
| 1トレード平均損益 | 0.17767277778434348 |
| 総リターン | 1.4777250383624763% |
| 月次換算（近似） | 0.12207017520573515% |
| 最大DD | 2.6437951774693316% |
| 勝率 | 41.17647058823529% |
| 最終資産 | 304.4331751150874 |

**ゲート不合格理由:** min_trades

## 5. 知見

実データ(binance_vision) Set B。costs=eval_v1 lock。 ゲート不合格。

**残す:**
- 実データ + 固定コストでの判定

**捨てる:**
- 合成 smoke を合否に使うこと

## 6. 次アクション

- 敗因を workstream notes に1点整理
- ルールを1点だけ変更して再 eval

## 7. 成果物

- `artifacts/evals/20260823T010425Z_setB_db_baseline_v1/`
- `artifacts/evals/20260823T010425Z_setB_db_baseline_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
