# L-BRACKET — 12h / 1.00% / 1分足

| 項目 | 値 |
|------|-----|
| logic_id | `br_*`（固定ブラケットの入口条件群） |
| 主歪み | 順張りの継続（15分足で z が出た側） |
| ステータス | `proposed`（直近1年スクリーニング中） |
| 優先順 | 1 |

## 目的

保有12時間・損切り1.00%・同時1枠のまま、入口を1分足にして必要上振れを +2.9pt まで下げた枠で、直近1年に黒字があるかを見る。

## 現状

- 実装: 枠定数と1分足取得・検証ランナーあり
- 最新ラン: 未検証（Set Y 待ち）
- 8年（eval_v3）は **1年で黒字が出てから**。先に回さない

## 次アクション

1. `scripts/prepare_btc_1m.py` で Set Y の1分足 lock
2. `run_bracket_pack.py --interval 1m --maker-entry --set Y`
3. 黒字0なら8年は回さない。黒字があればその logic だけ eval_v3 へ

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/` と [BRACKET_FRAME.md](../../hypothesis/BRACKET_FRAME.md)。

## 関連マスター

- [BRACKET_FRAME](../../hypothesis/BRACKET_FRAME.md)
- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
