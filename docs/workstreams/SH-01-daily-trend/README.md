# SH-01 — 日足規模のトレンド継続

| 項目 | 値 |
|------|-----|
| logic_id | `sh01n_center`（中心） / `sh01_base`（固定利確なし） |
| 主歪み | コストが R の数%に収まる値幅（日足ATR損切り） |
| ステータス | 50日と100日を demo へ。注文は1枠なので既定100日、50日は影 |
| 優先順 | 1 |

## 目的

往復コストが小さくて済む遅い値幅で、費用後EVが黒か、DDが20%以内かを見る。
固定利確1.5%・保有12hのブラケットは使わない。月50回は合否にしない。

## 現状

- 実装: `src/autotrade/strategy/slow.py`
- 環境: `configs/eval_v3_btc.yaml` + `eval/locks/eval_v3_btc.lock.yaml@e7bcbe449cbb`
- 2026-08-25 formal（`--campaign ev-dd`）: 中心・base とも 3期間 EV+、DD≤20%。プール t=+2.57
- 期間ごと n は 100 未満 → 判定保留。月 0.9〜1.8 回は報告のみ
- 2026-08-25 休む条件: `eval/reports/20260825-slow-rest.md`。`regime_50d` / `regime_100d` は 3期間とも Return/DD で買い持ちを上回る

## 次アクション

1. `secrets/demo/bybit.txt` に testnet キーを入れて `autotrade demo --submit`
2. ログで 50日（影）と 100日（注文）のシグナルが同時に残るか見る
3. 建玉がずれたら止める。live はまだやらない

手順: [DEMO.md](../../ops/DEMO.md)

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/`。
仮説正本: [SLOW_HYPOTHESES.md](../../hypothesis/SLOW_HYPOTHESES.md)

## 関連マスター

- [CURRENT](../../master/CURRENT.md)
- [TARGET_MODEL](../../master/TARGET_MODEL.md)
- [MARKET_ADVANTAGE_AXES](../../master/MARKET_ADVANTAGE_AXES.md)
