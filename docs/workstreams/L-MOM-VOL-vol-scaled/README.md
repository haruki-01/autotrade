# L-MOM-VOL — ボラ調整トレンド・トレール

| 項目 | 値 |
|------|-----|
| logic_id | `vol_scaled_trend_v1` |
| ステータス | formal **FAIL**（最悪） |
| Gate | 期待値❌ DD❌ 回数✅ |

## 現状

- Formal eval Set B: 期待値 **-6.59** / DD **98.4%** / 1,064 trades / 残高 ≈169
- 最新: [LATEST.md](./LATEST.md)
- 詳細: [バッチレポート](../../eval/reports/20260822-formal-eval-batch-setB.md)

## 次アクション

現行版は追わない。大きく変えるならルールを1点だけ定義し直してから再 eval。
