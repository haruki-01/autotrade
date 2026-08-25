# SH-01 — 日足規模のトレンド継続

| 項目 | 値 |
|------|-----|
| logic_id | `sh01n_center`（中心） / `sh01_base`（固定利確なし） |
| 主歪み | コストが R の数%に収まる値幅（日足ATR損切り） |
| ステータス | 再検証中（2026-08-25。合否は費用後EV>0 と DD） |
| 優先順 | 1 |

## 目的

往復コストが小さくて済む遅い値幅で、費用後EVが黒か、DDが20%以内かを見る。
固定利確1.5%・保有12hのブラケットは使わない。月50回は合否にしない。

## 現状

- 実装: `src/autotrade/strategy/slow.py`
- 環境: `configs/eval_v3_btc.yaml` + `eval/locks/eval_v3_btc.lock.yaml`
- 2026-08-24 記録（月50ゲート時）: 中心プール n=164 / EV +0.989 / t=+2.57 / DD 2.8/5.3/7.6%。3期間EV+。月1.6–1.8回で当時 FAIL
- 2026-08-25: 月50を合否から外して再測定する

## 次アクション

1. `run_slow_pack.py --campaign ev-dd` で `sh01n_center` と `sh01_base` を Set A/B/C
2. プール t と買い持ち Return/DD を同じレポートに書く
3. live 前は Bybit 再確認（lock は binance_vision）

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/`。
仮説正本: [SLOW_HYPOTHESES.md](../../hypothesis/SLOW_HYPOTHESES.md)

## 関連マスター

- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
- [TARGET_MODEL](../../master/TARGET_MODEL.md)
- [MARKET_ADVANTAGE_AXES](../../master/MARKET_ADVANTAGE_AXES.md)
