# SH-01 — 日足規模のトレンド継続

| 項目 | 値 |
|------|-----|
| logic_id | `sh01n_center`（中心） / `sh01_base`（固定利確なし） |
| 主歪み | コストが R の数%に収まる値幅（日足ATR損切り） |
| ステータス | EV+DD PASS（期間ごとサンプル保留）。Set C は買い持ち Return/DD 負け |
| 優先順 | 1 |

## 目的

往復コストが小さくて済む遅い値幅で、費用後EVが黒か、DDが20%以内かを見る。
固定利確1.5%・保有12hのブラケットは使わない。月50回は合否にしない。

## 現状

- 実装: `src/autotrade/strategy/slow.py`
- 環境: `configs/eval_v3_btc.yaml` + `eval/locks/eval_v3_btc.lock.yaml@e7bcbe449cbb`
- 2026-08-25 formal（`--campaign ev-dd`）: 中心・base とも 3期間 EV+、DD≤20%。プール t=+2.57
- 期間ごと n は 100 未満 → 判定保留。月 0.9〜1.8 回は報告のみ
- Set C Return/DD は買い持ちに負ける
- 正本: `eval/reports/20260825-slow-evdd.md`

## 次アクション

1. 春希さんの論点A: SH-01 を DD 売りとして demo に出すか（正本 [CURRENT.md](../../master/CURRENT.md)）
2. 「Set C で買い持ちに負けるのが嫌」なら論点Bだけ（既存 `regime` 1点）。入口は増やさない
3. 採用するなら論点C（Bybit / demo）。live 前に Vision データを再確認

## メモ置き場

調査メモは [notes/](./notes/) へ。数値の正本は `eval/reports/`。
仮説正本: [SLOW_HYPOTHESES.md](../../hypothesis/SLOW_HYPOTHESES.md)

## 関連マスター

- [IMPLEMENTATION_PLAN](../../master/IMPLEMENTATION_PLAN.md)
- [TARGET_MODEL](../../master/TARGET_MODEL.md)
- [MARKET_ADVANTAGE_AXES](../../master/MARKET_ADVANTAGE_AXES.md)
