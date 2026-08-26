# DB-13 / db_entry_break_bounce_high_v1 — Set B

- **Run ID:** `20260823-014`
- **記録日時:** 2026-08-23T01:04:52Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** DB反発足高値抜けでエントリー

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
| Git | `933022e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 22 |
| 1トレード平均損益 | -0.11896709289979857 |
| 総リターン | -1.1805677140250381% |
| 月次換算（近似） | -0.09871723358501061% |
| 最大DD | 3.3699290513690556% |
| 勝率 | 27.27272727272727% |
| 最終資産 | 296.4582968579249 |

**ゲート不合格理由:** expectancy, min_trades

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

- `artifacts/evals/20260823T010452Z_setB_db_entry_break_bounce_high_v1/`
- `artifacts/evals/20260823T010452Z_setB_db_entry_break_bounce_high_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
