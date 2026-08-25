# HYP-002 / donchian_20_10_long_v2 — Set B

- **Run ID:** `20260822-017`
- **記録日時:** 2026-08-22T07:50:23Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** Donchian Long v2 (新規上抜け+4H確認)

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
| トレード数 | 6 |
| 1トレード平均損益 | 5.919546211823732 |
| 総リターン | 11.79280986776645% |
| 月次換算（近似） | 0.9314091169496219% |
| 最大DD | 1.8249120127243061% |
| 勝率 | 33.33333333333333% |
| 最終資産 | 335.37842960329937 |

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

- `artifacts/evals/20260822T075022Z_setB_donchian_20_10_long_v2/`
- `artifacts/evals/20260822T075022Z_setB_donchian_20_10_long_v2/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
