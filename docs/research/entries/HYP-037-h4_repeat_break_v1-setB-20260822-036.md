# HYP-037 / h4_repeat_break_v1 — Set B

- **Run ID:** `20260822-036`
- **記録日時:** 2026-08-22T10:16:00Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 4H再突破

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
| トレード数 | 27 |
| 1トレード平均損益 | 1.5705860956089173 |
| 総リターン | 13.706908712190891% |
| 月次換算（近似） | 1.0740132117646795% |
| 最大DD | 4.098392990788548% |
| 勝率 | 40.74074074074074% |
| 最終資産 | 341.12072613657267 |

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

- `artifacts/evals/20260822T101600Z_setB_h4_repeat_break_v1/`
- `artifacts/evals/20260822T101600Z_setB_h4_repeat_break_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
