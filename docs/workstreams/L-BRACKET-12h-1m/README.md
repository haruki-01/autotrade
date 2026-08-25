# L-BRACKET — 12h / 1.00% / 1分足

| 項目 | 値 |
|------|-----|
| logic_id | `br_*`（固定ブラケットの入口条件群） |
| 主歪み | 順張りの継続（15分足で z が出た側） |
| ステータス | screen FAIL（Set Y 黒字 0。8年は未実施） |
| 優先順 | 1 |

## 目的

保有12時間・損切り1.00%・同時1枠のまま、入口を1分足にして必要上振れを +2.9pt まで下げた枠で、直近1年に黒字があるかを見る。

## 現状

- 実装: 枠定数と1分足取得・検証ランナーあり
- 最新ラン: Set Y（2025-08-23〜2026-08-22）**黒字 0** / 帰無40%超え 0
- 8年（eval_v3）は回していない（指示どおり）

## 次アクション

1. 分母は元本300で確定。次は12h/1.00%枠を **15分足・直近1年**
2. 黒字の条件だけ8年。なければ8年は回さない

詳細: [notes/2026-08-25-next-options.md](./notes/2026-08-25-next-options.md)

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/20260825-bracket1m-setY.md` と [BRACKET_FRAME.md](../../hypothesis/BRACKET_FRAME.md)。

## 関連マスター

- [BRACKET_FRAME](../../hypothesis/BRACKET_FRAME.md)
- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
