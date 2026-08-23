# SPOT-001 ダブルボトム 20サイクル

| 項目 | 値 |
|------|-----|
| スポット | [SPOT-001](../../hypothesis/spots/SPOT-001-double-bottom-neckline-retest.md) |
| 変数地図 | [VARIABLES.md](./VARIABLES.md) |
| Set B PASS | 1/20（`db_struct_1h_v1`） |
| Set C holdout | **FAIL**（EVマイナス） |
| レポート | [20 cycles](../../eval/reports/20260823-double-bottom-20-cycles.md) |

## min_trades

`min_trades=100` は **Set B（1年）の合計トレード数**。1ヶ月100ではない。

## 採用判断

現行ロジックは **デモ/本番に進まない**。  
次に残す測り方の候補（n不足だがEV+）: 上位上昇のみ / 突破鮮度 / 高値奪還 / ATRトレール。  
1H化は回数解決には有効だが、エッジが薄い。
