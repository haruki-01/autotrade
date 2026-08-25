# L-BRACKET — 12h / 1.00% / 1分足

| 項目 | 値 |
|------|-----|
| logic_id | `br_*`（固定ブラケットの入口条件群） |
| 主歪み | 順張りの継続（15分足で z が出た側） |
| ステータス | 案2 FAIL。入口スポット BR-001〜008 を起票（未検証） |
| 優先順 | 1 |

## 目的

保有12時間・損切り1.00%・同時1枠のまま、入口を1分足にして必要上振れを +2.9pt まで下げた枠で、直近1年に黒字があるかを見る。

## 現状

- 分母: 元本300で確定
- Set Y 1分足: 決済EV黒字0
- Set Y 15分足（案1）: 決済EV黒字0。`br_trend_pb` だけEV全部 +0.017（決済はマイナス、月27回）
- Set Y 案2（上位足×1分）: 決済EV黒字0。最良 `br_htf1h_ema_pb` 41.2%（z=+0.61、月73回）
- 8年は回していない

## 次アクション

1. 春希さんが入口スポット（BR-001〜008）から短リストを選ぶ
2. 選んだ①だけ②を実装し、直近1年で測る。8年は決済EVが黒になってから。枠はまだ触らない

入口一括: [notes/2026-08-25-entry-spot-batch.md](./notes/2026-08-25-entry-spot-batch.md)  
棄却済み案2: [notes/2026-08-25-htf-1m-spots.md](./notes/2026-08-25-htf-1m-spots.md)  
レポート: `eval/reports/20260825-bracket-htf1m-setY.md`

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/20260825-bracket1m-setY.md` と [BRACKET_FRAME.md](../../hypothesis/BRACKET_FRAME.md)。

## 関連マスター

- [BRACKET_FRAME](../../hypothesis/BRACKET_FRAME.md)
- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
