# HYP-033 / d_monday_break_v1 — Set B

- **Run ID:** `20260822-058`
- **記録日時:** 2026-08-22T10:17:15Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 月曜突破

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
| トレード数 | 4 |
| 1トレード平均損益 | 6.742982192836232 |
| 総リターン | 8.956403800121592% |
| 月次換算（近似） | 0.7159198199006234% |
| 最大DD | 1.5368821672671218% |
| 勝率 | 50.0% |
| 最終資産 | 326.8692114003648 |

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

- `artifacts/evals/20260822T101714Z_setB_d_monday_break_v1/`
- `artifacts/evals/20260822T101714Z_setB_d_monday_break_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
