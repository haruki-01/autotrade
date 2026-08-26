# L-COST — 費用ゲート

| 項目 | 値 |
|------|-----|
| logic_id | `cost_gate_v1` |
| ステータス | formal **FAIL** |
| Gate | 期待値❌ DD❌ 回数✅ |

## 現状

- Formal eval Set B: 期待値 **-3.73** / DD **51.6%** / 570 trades（H01より悪化）
- 最新: [LATEST.md](./LATEST.md)
- 詳細: [バッチレポート](../../eval/reports/20260822-formal-eval-batch-setB.md)

## 次アクション

現行ゲート実装は棄却寄り。パラメータ探索より別ファミリー（L-BREAK）を優先。
