# H01 / mtf_ema_pullback_v1 — Set B

- **Run ID:** `20260822-011`
- **記録日時:** 2026-08-22T07:31:14Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** MTF EMA押し目 v1

**一言:** Formal eval FAIL

**狙う歪み:** （未タグ）

## 2. 売買ロジック

- **eval_version:** eval_v1
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
| トレード数 | 594 |
| 1トレード平均損益 | -3.0963373046045253 |
| 総リターン | -43.28338885291508% |
| 月次換算（近似） | -4.606819054731803% |
| 最大DD | 49.37358558027742% |
| 勝率 | 40.235690235690235% |
| 最終資産 | 5671.661114708491 |

**ゲート不合格理由:** expectancy, drawdown

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

- `artifacts/evals/20260822T073113Z_setB_mtf_ema_pullback_v1/`
- `artifacts/evals/20260822T073113Z_setB_mtf_ema_pullback_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
