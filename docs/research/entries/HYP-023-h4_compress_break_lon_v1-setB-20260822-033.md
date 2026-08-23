# HYP-023 / h4_compress_break_lon_v1 — Set B

- **Run ID:** `20260822-033`
- **記録日時:** 2026-08-22T10:15:48Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 圧縮後ロンドン突破

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
| トレード数 | 9 |
| 1トレード平均損益 | 4.390014814246687 |
| 総リターン | 13.023144229633532% |
| 月次換算（近似） | 1.0233258595573336% |
| 最大DD | 2.4718245411734228% |
| 勝率 | 33.33333333333333% |
| 最終資産 | 339.0694326889006 |

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

- `artifacts/evals/20260822T101548Z_setB_h4_compress_break_lon_v1/`
- `artifacts/evals/20260822T101548Z_setB_h4_compress_break_lon_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
