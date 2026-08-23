# HYP-042 / h4_break_below_sma_v1 — Set B

- **Run ID:** `20260822-041`
- **記録日時:** 2026-08-22T10:16:12Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** SMA下での上抜け

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
| Git | `cf5c0ee` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 3 |
| 1トレード平均損益 | -0.8606325304705152 |
| 総リターン | -0.8975997701003102% |
| 月次換算（近似） | -0.07495776160852952% |
| 最大DD | 0.897599770100309% |
| 勝率 | 0.0% |
| 最終資産 | 297.3072006896991 |

**ゲート不合格理由:** expectancy, min_trades

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

- `artifacts/evals/20260822T101611Z_setB_h4_break_below_sma_v1/`
- `artifacts/evals/20260822T101611Z_setB_h4_break_below_sma_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
