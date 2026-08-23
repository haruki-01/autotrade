# HYP-009 / fake_then_rebreak_v1 — Set B

- **Run ID:** `20260822-019`
- **記録日時:** 2026-08-22T09:59:32Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** D-001 だまし後本突破初日

**一言:** Formal eval FAIL

**狙う歪み:** E1, E6, E8

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
| トレード数 | 1 |
| 1トレード平均損益 | -0.808937613922857 |
| 総リターン | -0.2769427561095772% |
| 月次換算（近似） | -0.023061218503162006% |
| 最大DD | 0.27694275610957675% |
| 勝率 | 0.0% |
| 最終資産 | 299.16917173167127 |

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

- `artifacts/evals/20260822T095931Z_setB_fake_then_rebreak_v1/`
- `artifacts/evals/20260822T095931Z_setB_fake_then_rebreak_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
