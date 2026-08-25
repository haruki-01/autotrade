# L-BREAK / donchian_20_10_v1 — Set B

- **Run ID:** `20260822-009`
- **記録日時:** 2026-08-22T05:37:51Z
- **ステータス:** `smoke`
- **ゲート:** SMOKE（判定に使わない）

## 1. 仮説

**名称:** Donchian 20/10 ブレイク

**一言:** 合成データ smoke。採用判断に使わない。

**狙う歪み:** E1

## 2. 売買ロジック

- **entry:** 日足20 Donchian ブレイク
- **exit:** 日足10 Donchian 逆側 + ATRストップ
- **long_only:** False

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
| トレード数 | 5 |
| 1トレード平均損益 | 4474.326657667223 |
| 総リターン | 223.5580220068855% |
| 月次換算（近似） | 10.287202614214497% |
| 最大DD | 0.02248627571211898% |
| 勝率 | 100.0% |
| 最終資産 | 32355.802200688548 |

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

- `artifacts/backtests/20260822T053751Z_setB_donchian_20_10_v1/`
- `artifacts/backtests/20260822T053751Z_setB_donchian_20_10_v1/metrics.json`

## メモ

synthetic smoke
