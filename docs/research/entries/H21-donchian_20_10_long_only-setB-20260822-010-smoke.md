# H21 / donchian_20_10_long_only — Set B

- **Run ID:** `20260822-010`
- **記録日時:** 2026-08-22T05:37:54Z
- **ステータス:** `smoke`
- **ゲート:** SMOKE（判定に使わない）

## 1. 仮説

**名称:** Donchian 20/10 Long only

**一言:** 合成データ smoke。採用判断に使わない。

**狙う歪み:** E1

## 2. 売買ロジック

- **entry:** 日足20 Donchian 上抜けのみ
- **exit:** 日足10 Donchian 下抜け + ATRストップ
- **long_only:** True

## 3. 検証条件

| 項目 | 値 |
|------|-----|
| 評価期間 | 2024-01-01 → 2024-12-31 |
| データ | synthetic |
| 合成データ | True |
| 15m本数 | 35041 |
| 設定 | `configs/backtest_v1.yaml` |
| Git | `cf5c0ee` |

## 4. 結果

| 指標 | 値 |
|------|-----|
| トレード数 | 3 |
| 1トレード平均損益 | 4102.211351084604 |
| 総リターン | 122.99550805170027% |
| 月次換算（近似） | 6.916456382159808% |
| 最大DD | 0.018999477510841772% |
| 勝率 | 100.0% |
| 最終資産 | 22299.550805170027 |

**ゲート不合格理由:** min_trades

## 5. 知見

パイプライン・ロジック実装の動作確認。次は実データ Set B。

**残す:**
- 実装パスと research / workstream への自動蓄積

**捨てる:**
- 合成でのゲートPASSを意思決定に使うこと

## 6. 次アクション

- 実データ（Bybit or Vision）で Set B を再実行
- workstream README の現状を更新

## 7. 成果物

- `artifacts/backtests/20260822T053753Z_setB_donchian_20_10_long_only/`
- `artifacts/backtests/20260822T053753Z_setB_donchian_20_10_long_only/metrics.json`

## メモ

synthetic smoke
