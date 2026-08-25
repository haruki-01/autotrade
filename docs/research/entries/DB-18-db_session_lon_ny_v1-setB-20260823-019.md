# DB-18 / db_session_lon_ny_v1 — Set B

- **Run ID:** `20260823-019`
- **記録日時:** 2026-08-23T01:05:03Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** DBロンドン/NYのみ執行

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
| トレード数 | 21 |
| 1トレード平均損益 | 0.12161742685742542 |
| 総リターン | 0.5221782860482582% |
| 月次換算（近似） | 0.04332331537286738% |
| 最大DD | 1.7925250430864847% |
| 勝率 | 42.857142857142854% |
| 最終資産 | 301.5665348581448 |

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

- `artifacts/evals/20260823T010503Z_setB_db_session_lon_ny_v1/`
- `artifacts/evals/20260823T010503Z_setB_db_session_lon_ny_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
