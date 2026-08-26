# HYP-052 / h4_break_bull_confirm_v1 — Set B

- **Run ID:** `20260822-042`
- **記録日時:** 2026-08-22T10:16:14Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 非アジア突破＋陽線確認

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
| トレード数 | 30 |
| 1トレード平均損益 | 1.4624328452071937 |
| 総リターン | 14.143337896878162% |
| 月次換算（近似） | 1.1062197284216868% |
| 最大DD | 4.259000503599035% |
| 勝率 | 36.666666666666664% |
| 最終資産 | 342.4300136906345 |

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

- `artifacts/evals/20260822T101614Z_setB_h4_break_bull_confirm_v1/`
- `artifacts/evals/20260822T101614Z_setB_h4_break_bull_confirm_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
