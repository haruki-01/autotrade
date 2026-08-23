# DB-42 / db_1h_band_wide_v1 — Set B

- **Run ID:** `20260823-044`
- **記録日時:** 2026-08-23T02:01:56Z
- **ステータス:** `pass`
- **ゲート:** PASS

## 1. 仮説

**名称:** 1H+タッチ帯広い

**一言:** Formal eval PASS

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
| Git | `6011e9e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 110 |
| 1トレード平均損益 | 0.015916654607765077 |
| 総リターン | -1.2139560011077077% |
| 月次換算（近似） | -0.10152480219759452% |
| 最大DD | 7.481869795226821% |
| 勝率 | 31.818181818181817% |
| 最終資産 | 296.3581319966769 |

**ゲート不合格理由:** —

## 5. 知見

実データ(binance_vision) Set B。costs=eval_v1 lock。 ゲート合格。

**残す:**
- 実データ + 固定コストでの判定

**捨てる:**
- 合成 smoke を合否に使うこと

## 6. 次アクション

- Set C holdout
- demo 設計

## 7. 成果物

- `artifacts/evals/20260823T020155Z_setB_db_1h_band_wide_v1/`
- `artifacts/evals/20260823T020155Z_setB_db_1h_band_wide_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
