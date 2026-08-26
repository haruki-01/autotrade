# SH-01 — 日足規模のトレンド継続

| 項目 | 値 |
|------|-----|
| logic_id | `sh01n_center`（中心） / `sh01_base`（固定利確なし） |
| 主歪み | コストが R の数%に収まる値幅（日足ATR損切り） |
| ステータス | 本命。執行先は GMO 方針。**先に再現性の強化**（アダプタは後） |
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
- 保有実測（regime_100d プール）: 中央値約4日 / 平均約7日
- 2026-08-26: Bybit は日本居住で不可 → **GMO ベース**。春希さん指示で **勝てる再現を先**、API は後

## 次アクション

1. 入口を増やさず、SH-01 の再現性（期間符号・プール t・買い持ち対比）を固める
2. GMO コスト（レバ2・建玉管理料）を eval に入れて再 formal
3. 通ったら GMO demo。Bybit `--submit` は進めない

正本: [CURRENT.md](../../master/CURRENT.md) · 取引所: [EXCHANGE_CANDIDATES_JP.md](../../ops/EXCHANGE_CANDIDATES_JP.md)

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/`。
仮説正本: [SLOW_HYPOTHESES.md](../../hypothesis/SLOW_HYPOTHESES.md)

## 関連マスター

- [CURRENT](../../master/CURRENT.md)
- [TARGET_MODEL](../../master/TARGET_MODEL.md)
- [MARKET_ADVANTAGE_AXES](../../master/MARKET_ADVANTAGE_AXES.md)
