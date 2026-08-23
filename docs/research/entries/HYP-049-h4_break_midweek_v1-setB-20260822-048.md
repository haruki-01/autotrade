# HYP-049 / h4_break_midweek_v1 — Set B

- **Run ID:** `20260822-048`
- **記録日時:** 2026-08-22T10:16:28Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 火水木の非アジア突破

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
| トレード数 | 15 |
| 1トレード平均損益 | 2.7729054713570047 |
| 総リターン | 13.63389097760319% |
| 月次換算（近似） | 1.0686137664727147% |
| 最大DD | 3.1535752018851406% |
| 勝率 | 46.666666666666664% |
| 最終資産 | 340.90167293280956 |

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

- `artifacts/evals/20260822T101628Z_setB_h4_break_midweek_v1/`
- `artifacts/evals/20260822T101628Z_setB_h4_break_midweek_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
