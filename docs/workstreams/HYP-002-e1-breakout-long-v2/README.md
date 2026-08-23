# HYP-002 — Donchian Long v2

| 項目 | 値 |
|------|-----|
| logic_id | `donchian_20_10_long_v2` |
| ステータス | formal **FAIL**（n=6） |
| サイジング | margin $30 × lev3 / risk $3 |

## Formal Set B

- 期待値 **+$5.92** / DD **1.8%** / トレード **6** / リターン +11.8%
- Gate: 回数不足で FAIL（EV・DDはクリア）
- 最新: [LATEST.md](./LATEST.md)
- レポート: `eval/reports/20260822T075022Z_donchian_20_10_long_v2_setB.md`

## 次

n 確保の **別仮説カード** を立ててから実装（この v2 の再チューニングはしない）。
