# SH-01 / sh01n_center — EV+DD campaign (A/B/C)

- **Run ID:** `20260825-slow-evdd`
- **記録日時:** 2026-08-25
- **ステータス:** `pass`（EV+DD）。期間ごとの n は判定保留
- **ゲート:** EV+DD PASS / sample HOLD / 月50は非ゲート

## 1. 仮説

日足ATR損切りならコストがRの数%に収まり、費用後EVを議論できる。

## 3. 検証条件

| 項目 | 値 |
|------|-----|
| 評価期間 | A 2018-10-01〜2021-04-30 / B 2021-05-01〜2023-12-31 / C 2024-01-01〜2026-08-22 |
| データソース | binance_vision |
| 合成データ | false |
| 設定ファイル | configs/eval_v3_btc.yaml |
| lock | eval_v3_btc.lock.yaml@e7bcbe449cbb |
| コスト | fee 5.5bps/side + slip 2bps/side |

## 4. 結果（中心）

| Set | n | EV | DD | ゲート |
|-----|---|-----|-----|--------|
| A | 56 | +1.951 | 2.8% | EV+DD PASS / sample HOLD |
| B | 51 | +0.528 | 5.3% | EV+DD PASS / sample HOLD |
| C | 57 | +0.456 | 7.6% | EV+DD PASS / sample HOLD |
| プール | 164 | +0.989 t=+2.57 | — | t≥2 |

対照 `sh01_base` プール n=104 / EV +3.090 / t=+2.57。

Set C 買い持ち Return/DD 1.51 に対し中心 1.14。

正本: [eval/reports/20260825-slow-evdd.md](../../eval/reports/20260825-slow-evdd.md)
