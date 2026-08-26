# L-BREAK-2 / donchian_h4_20_10_v1 — Set B

- **Run ID:** `20260823-001`
- **記録日時:** 2026-08-23T00:44:51Z
- **ステータス:** `fail`
- **ゲート:** FAIL

## 1. 仮説

**名称:** Donchian 20/10 on 4H（サンプル確保）

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
| Git | `93f1fc5` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 58 |
| 1トレード平均損益 | 0.8483133636160017 |
| 総リターン | 15.490462695768525% |
| 月次換算（近似） | 1.2049242446977582% |
| 最大DD | 3.797308268425125% |
| 勝率 | 37.93103448275862% |
| 最終資産 | 346.47138808730557 |

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

- `artifacts/evals/20260823T004451Z_setB_donchian_h4_20_10_v1/`
- `artifacts/evals/20260823T004451Z_setB_donchian_h4_20_10_v1/metrics.json`

## メモ

formal_eval lock=eval/locks/eval_v1.lock.yaml
