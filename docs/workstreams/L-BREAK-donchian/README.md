# L-BREAK — Donchian 20/10 ブレイク

| 項目 | 値 |
|------|-----|
| logic_id | `donchian_20_10_v1` |
| ステータス | formal **FAIL**（サンプル不足） |
| Gate | 期待値✅ DD✅ 回数❌（13） |

## 現状

- Formal eval Set B: 期待値 **+54.3** / DD **3.8%** / **13 trades** / リターン +7.0%
- 方向性は5本中最良だが n 不足で不合格
- 最新: [LATEST.md](./LATEST.md)
- 詳細: [バッチレポート](../../eval/reports/20260822-formal-eval-batch-setB.md)

## 次アクション

サンプル確保のための変更を **1点だけ**（執行頻度）→ 再 formal eval。H21 と比較継続。
