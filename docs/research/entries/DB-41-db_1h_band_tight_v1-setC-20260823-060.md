# DB-41 / db_1h_band_tight_v1 — Set C

- **Run ID:** `20260823-060`
- **記録日時:** 2026-08-23T02:03:18Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 1H+タッチ帯狭い

**一言:** Formal eval FAIL

**狙う歪み:** E1

## 2. 売買ロジック

- **eval_version:** eval_v1.1
- **set:** C

## 3. 検証条件

| 項目 | 値 |
|------|-----|
| 評価期間 | 2025-01-01 → 2026-08-22 |
| データ | binance_vision |
| 合成データ | False |
| 15m本数 | 57439 |
| 設定 | `configs/eval_v1.yaml` |
| Git | `6011e9e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 208 |
| 1トレード平均損益 | -0.06979692810276648 |
| 総リターン | -8.27125368179351% |
| 月次換算（近似） | -0.4382392565559057% |
| 最大DD | 9.169988803264927% |
| 勝率 | 29.807692307692307% |
| 最終資産 | 275.18623895461945 |

**ゲート不合格理由:** expectancy

## 5. 知見

実データ(binance_vision) Set C。costs=eval_v1 lock。 ゲート不合格。

**残す:**
- 実データ + 固定コストでの判定

**捨てる:**
- 合成 smoke を合否に使うこと

## 6. 次アクション

- 敗因を workstream notes に1点整理
- ルールを1点だけ変更して再 eval

## 7. 成果物

- `artifacts/evals/20260823T020317Z_setC_db_1h_band_tight_v1/`
- `artifacts/evals/20260823T020317Z_setC_db_1h_band_tight_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
