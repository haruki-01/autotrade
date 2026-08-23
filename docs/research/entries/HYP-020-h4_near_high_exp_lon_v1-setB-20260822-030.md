# HYP-020 / h4_near_high_exp_lon_v1 — Set B

- **Run ID:** `20260822-030`
- **記録日時:** 2026-08-22T10:15:42Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 高値拡大ロンドン

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
| トレード数 | 13 |
| 1トレード平均損益 | 2.27018441612758 |
| 総リターン | 9.631909057243515% |
| 月次換算（近似） | 0.7677023387163251% |
| 最大DD | 3.902843248872016% |
| 勝率 | 30.76923076923077% |
| 最終資産 | 328.8957271717305 |

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

- `artifacts/evals/20260822T101541Z_setB_h4_near_high_exp_lon_v1/`
- `artifacts/evals/20260822T101541Z_setB_h4_near_high_exp_lon_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
