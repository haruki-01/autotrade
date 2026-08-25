# DB-42 / db_1h_band_wide_v1 — Set C

- **Run ID:** `20260823-059`
- **記録日時:** 2026-08-23T02:03:14Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 1H+タッチ帯広い

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
| トレード数 | 211 |
| 1トレード平均損益 | -0.11412611907745682 |
| 総リターン | -11.498356935106269% |
| 月次換算（近似） | -0.6194730366190226% |
| 最大DD | 12.105634196903566% |
| 勝率 | 30.80568720379147% |
| 最終資産 | 265.5049291946812 |

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

- `artifacts/evals/20260823T020313Z_setC_db_1h_band_wide_v1/`
- `artifacts/evals/20260823T020313Z_setC_db_1h_band_wide_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
