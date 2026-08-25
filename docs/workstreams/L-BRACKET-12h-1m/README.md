# L-BRACKET — 12h / 1.00% / 1分足

| 項目 | 値 |
|------|-----|
| logic_id | `br_*`（固定ブラケットの入口条件群） |
| 主歪み | 順張りの継続（15分足で z が出た側） |
| ステータス | 入口を優位軸で再採点。BR不採用。ADV 未検証 |
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

1. 短リスト ADV-002 / 001 / 005（拒否は ADV-004 を1点）だけ②へ。BR-001〜008 は実装しない
2. 8年は決済EVが黒になってから。枠はまだ触らない

優位軸: [MARKET_ADVANTAGE_AXES.md](../../master/MARKET_ADVANTAGE_AXES.md)  
再採点: [notes/2026-08-25-advantage-rescore.md](./notes/2026-08-25-advantage-rescore.md)

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/20260825-bracket1m-setY.md` と [BRACKET_FRAME.md](../../hypothesis/BRACKET_FRAME.md)。

## 関連マスター

- [BRACKET_FRAME](../../hypothesis/BRACKET_FRAME.md)
- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
