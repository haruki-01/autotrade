# DB-47 / db_15m_reclaim_v1 — Set B

- **Run ID:** `20260823-049`
- **記録日時:** 2026-08-23T02:02:16Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** 15m+高値奪還

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
| Git | `6011e9e` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 389 |
| 1トレード平均損益 | -0.10019987285663098 |
| 総リターン | -19.402597881105233% |
| 月次換算（近似） | -1.777904413275011% |
| 最大DD | 19.73258837228084% |
| 勝率 | 30.59125964010283% |
| 最終資産 | 241.79220635668432 |

**ゲート不合格理由:** expectancy

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

- `artifacts/evals/20260823T020216Z_setB_db_15m_reclaim_v1/`
- `artifacts/evals/20260823T020216Z_setB_db_15m_reclaim_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
