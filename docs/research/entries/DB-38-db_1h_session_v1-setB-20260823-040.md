# DB-38 / db_1h_session_v1 — Set B

- **Run ID:** `20260823-040`
- **記録日時:** 2026-08-23T02:01:46Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 1H+Lon/NYのみ

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
| Git | `6011e9e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 75 |
| 1トレード平均損益 | 0.030146438634779425 |
| 総リターン | -0.48383903413107276% |
| 月次換算（近似） | -0.040327967815501076% |
| 最大DD | 4.184246624538896% |
| 勝率 | 36.0% |
| 最終資産 | 298.5484828976068 |

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

- `artifacts/evals/20260823T020145Z_setB_db_1h_session_v1/`
- `artifacts/evals/20260823T020145Z_setB_db_1h_session_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
