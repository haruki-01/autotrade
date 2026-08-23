# DB-14 / db_retest_fresh_v1 — Set B

- **Run ID:** `20260823-015`
- **記録日時:** 2026-08-23T01:04:54Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** DB突破後12本以内の再テスト

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
| トレード数 | 24 |
| 1トレード平均損益 | 0.4909417529129649 |
| 総リターン | 3.5417376140036483% |
| 月次換算（近似） | 0.28987160970663783% |
| 最大DD | 1.8621374622676778% |
| 勝率 | 54.166666666666664% |
| 最終資産 | 310.62521284201097 |

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

- `artifacts/evals/20260823T010454Z_setB_db_retest_fresh_v1/`
- `artifacts/evals/20260823T010454Z_setB_db_retest_fresh_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
