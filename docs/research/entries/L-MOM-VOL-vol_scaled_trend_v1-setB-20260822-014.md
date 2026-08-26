# L-MOM-VOL / vol_scaled_trend_v1 — Set B

- **Run ID:** `20260822-014`
- **記録日時:** 2026-08-22T07:33:06Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** ボラ調整トレンド・トレール

**一言:** Formal eval FAIL

**狙う歪み:** E1, E6

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
| トレード数 | 1064 |
| 1トレード平均損益 | -6.590907971222384 |
| 総リターン | -98.31171613325186% |
| 月次換算（近似） | -28.782681519355812% |
| 最大DD | 98.3590823939005% |
| 勝率 | 28.665413533834588% |
| 最終資産 | 168.82838667481275 |

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

- `artifacts/evals/20260822T073305Z_setB_vol_scaled_trend_v1/`
- `artifacts/evals/20260822T073305Z_setB_vol_scaled_trend_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
