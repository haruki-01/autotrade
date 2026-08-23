# H21 — Donchian 20/10 Long only

| 項目 | 値 |
|------|-----|
| logic_id | `donchian_20_10_long_only` |
| ステータス | formal **FAIL**（サンプル不足） |
| Gate | 期待値✅ DD✅ 回数❌（8） |

## 現状

- Formal eval Set B: 期待値 **+122.4** / DD **2.0%** / **8 trades** / リターン +9.7%
- L-BREAK より数字は良いが n=8。2024 上昇バイアスの可能性
- 最新: [LATEST.md](./LATEST.md)
- 詳細: [バッチレポート](../../eval/reports/20260822-formal-eval-batch-setB.md)

## 次アクション

L-BREAK と同時にサンプル確保後、再判定。単独採用はしない。
