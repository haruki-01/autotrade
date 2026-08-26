# EH-01〜EH-10 — 検証100サイクル（Set C）

実行UTC: 2026-08-23T05:28:21Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **1 / 54**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh06r_base` | EH-06R | 再掲: 乖離1.0σで即入り | FAIL | 1187 | -0.120 | 51.0 | 42.9 | 0.9 | expectancy,drawdown |
| 2 | `eh06r_ctrl_follow_retail` | EH-06R | 対照: 個人側に付く | FAIL | 1220 | -0.132 | 54.6 | 41.4 | -0.8 | expectancy,drawdown |
| 3 | `eh06r_cool_96` | EH-06R | 24hクールダウン | FAIL | 365 | -0.127 | 19.3 | 44.4 | 0.3 | expectancy |
| 4 | `eh06r_cool_192` | EH-06R | 48hクールダウン | FAIL | 220 | -0.102 | 11.8 | 45.0 | 0.2 | expectancy |
| 5 | `eh06r_cool_32` | EH-06R | 8hクールダウン | FAIL | 615 | -0.081 | 19.8 | 44.7 | 0.4 | expectancy |
| 6 | `eh06r_persist_8` | EH-06R | 乖離が2h続いてから | FAIL | 1015 | -0.082 | 31.5 | 44.8 | 1.0 | expectancy,drawdown |
| 7 | `eh06r_persist_32` | EH-06R | 乖離が8h続いてから | FAIL | 829 | -0.102 | 30.1 | 43.3 | 0.7 | expectancy,drawdown |
| 8 | `eh06r_both_extreme` | EH-06R | 個人・上位の両方が偏っている | FAIL | 806 | -0.135 | 38.9 | 42.7 | 0.7 | expectancy,drawdown |
| 9 | `eh06r_thr_2p0` | EH-06R | 乖離2.0σ | FAIL | 450 | -0.120 | 20.3 | 43.6 | 0.4 | expectancy,drawdown |
| 10 | `eh06r_gate_break` | EH-06R | 12h突破のゲートとして使う | FAIL | 418 | -0.071 | 13.0 | 46.7 | 0.3 | expectancy |
| 11 | `eh06r_gate_break_ctrl` | EH-06R | 対照: ゲートなしの突破 | FAIL | 1364 | -0.143 | 66.8 | 42.7 | 0.1 | expectancy,drawdown |
| 12 | `eh06r_gate_break_96` | EH-06R | 24h突破のゲート | FAIL | 311 | -0.064 | 11.5 | 47.3 | 0.2 | expectancy |
| 13 | `eh06r_struct_exit` | EH-06R | 構造退出のみ（目標なし） | FAIL | 957 | -0.136 | 47.8 | 16.1 | 0.8 | expectancy,drawdown |
| 14 | `eh06r_trail_4` | EH-06R | トレール4ATR | FAIL | 461 | -0.166 | 29.5 | 24.9 | 0.7 | expectancy,drawdown |
| 15 | `eh06r_tp_4atr` | EH-06R | 利確4ATR | FAIL | 584 | -0.112 | 25.5 | 27.1 | 1.1 | expectancy,drawdown |
| 16 | `eh06r_stop_2p5` | EH-06R | 損切2.5ATR | FAIL | 754 | -0.151 | 41.5 | 54.0 | 0.8 | expectancy,drawdown |
| 17 | `eh06r_win_10d` | EH-06R | 基準窓10日 | FAIL | 1324 | -0.127 | 59.2 | 44.1 | 1.2 | expectancy,drawdown |
| 18 | `eh06r_count_ratio` | EH-06R | 上位比=口座数版 | FAIL | 3 | 0.550 | 0.6 | 33.3 | 0.1 | min_trades |
| 19 | `eh06r_cool96_struct` | EH-06R | 24hクールダウン+構造退出 | FAIL | 317 | -0.117 | 16.5 | 24.0 | 0.6 | expectancy |
| 20 | `eh06r_cool96_thr2` | EH-06R | 24hクールダウン+乖離2.0σ | FAIL | 148 | -0.043 | 8.1 | 45.3 | 0.2 | expectancy |
| 21 | `eh09r_base` | EH-09R | 再掲: metrics成行比の傾き | FAIL | 538 | -0.074 | 14.9 | 44.1 | -0.4 | expectancy |
| 22 | `eh09r_ctrl_confirm` | EH-09R | 対照: 成行と同方向（順張り） | FAIL | 682 | -0.139 | 33.2 | 43.5 | -0.0 | expectancy,drawdown |
| 23 | `eh09r_perp_vol` | EH-09R | 先物出来高から成行比を作る | FAIL | 450 | -0.029 | 7.7 | 45.3 | -0.3 | expectancy |
| 24 | `eh09r_perp_vol_w32` | EH-09R | 出来高版+計測8h | FAIL | 444 | -0.114 | 17.4 | 42.1 | -0.3 | expectancy |
| 25 | `eh09r_perp_vol_slope` | EH-09R | 出来高版+傾き閾値0.05 | FAIL | 306 | -0.006 | 5.3 | 47.1 | -0.1 | expectancy |
| 26 | `eh09r_perp_vol_ctrl` | EH-09R | 対照: 出来高版で順張り | FAIL | 723 | -0.128 | 32.4 | 44.5 | 0.3 | expectancy,drawdown |
| 27 | `eh09r_slope_0p05` | EH-09R | 傾き閾値0.05 | FAIL | 372 | -0.067 | 9.2 | 43.8 | -0.3 | expectancy |
| 28 | `eh09r_struct_exit` | EH-09R | 構造退出のみ（目標なし） | FAIL | 702 | -0.096 | 22.4 | 16.0 | -0.6 | expectancy,drawdown |
| 29 | `eh09r_trail_4` | EH-09R | トレール4ATR | FAIL | 397 | -0.039 | 12.6 | 24.4 | -1.0 | expectancy |
| 30 | `eh09r_tp_4atr` | EH-09R | 利確4ATR | FAIL | 453 | -0.018 | 9.7 | 28.9 | -0.5 | expectancy |
| 31 | `eh09r_stop_2p5` | EH-09R | 損切2.5ATR | FAIL | 451 | -0.126 | 20.3 | 54.8 | -0.4 | expectancy,drawdown |
| 32 | `eh09r_extend_0p5` | EH-09R | 高値を0.5ATR超えてから | FAIL | 218 | -0.082 | 8.2 | 45.9 | -0.1 | expectancy |
| 33 | `eh09r_extend_1p0` | EH-09R | 高値を1.0ATR超えてから | FAIL | 82 | -0.044 | 3.3 | 47.6 | -0.0 | expectancy,min_trades |
| 34 | `eh09r_cool_96` | EH-09R | 24hクールダウン | FAIL | 279 | -0.083 | 10.6 | 43.4 | -0.3 | expectancy |
| 35 | `eh09r_cool_32` | EH-09R | 8hクールダウン | FAIL | 396 | -0.078 | 12.1 | 44.7 | -0.3 | expectancy |
| 36 | `eh09r_persist_8` | EH-09R | 減衰が2h続いてから | FAIL | 268 | -0.031 | 4.7 | 46.3 | -0.1 | expectancy |
| 37 | `eh09r_short_only` | EH-09R | ショートのみ | FAIL | 307 | -0.020 | 3.7 | 47.6 | -0.9 | expectancy |
| 38 | `eh09r_slope05_struct` | EH-09R | 傾き0.05+構造退出 | FAIL | 466 | -0.047 | 10.8 | 15.7 | -0.4 | expectancy |
| 39 | `eh09r_perpvol_struct` | EH-09R | 出来高版+構造退出 | FAIL | 598 | -0.058 | 11.8 | 17.2 | -0.3 | expectancy |
| 40 | `eh09r_slope05_cool96` | EH-09R | 傾き0.05+24hクールダウン | FAIL | 223 | -0.085 | 8.0 | 41.7 | -0.3 | expectancy |
| 41 | `eh06n_center` | EH-06N | 中心: 乖離2.0σ + 24hクールダウン | FAIL | 148 | -0.043 | 8.1 | 45.3 | 0.2 | expectancy |
| 42 | `eh06n_thr_1p5` | EH-06N | 乖離1.5σ | FAIL | 237 | -0.232 | 20.3 | 41.4 | 0.2 | expectancy,drawdown |
| 43 | `eh06n_thr_1p75` | EH-06N | 乖離1.75σ | FAIL | 188 | -0.240 | 16.4 | 40.4 | 0.2 | expectancy |
| 44 | `eh06n_thr_2p25` | EH-06N | 乖離2.25σ | FAIL | 118 | -0.074 | 4.3 | 44.9 | 0.2 | expectancy |
| 45 | `eh06n_thr_2p5` | EH-06N | 乖離2.5σ | FAIL | 99 | -0.052 | 4.6 | 44.4 | 0.2 | expectancy,min_trades |
| 46 | `eh06n_cool_48` | EH-06N | 12hクールダウン | FAIL | 215 | -0.073 | 10.8 | 43.3 | 0.2 | expectancy |
| 47 | `eh06n_cool_64` | EH-06N | 16hクールダウン | FAIL | 193 | -0.067 | 9.9 | 45.6 | 0.3 | expectancy |
| 48 | `eh06n_cool_128` | EH-06N | 32hクールダウン | FAIL | 127 | -0.024 | 5.8 | 46.5 | 0.2 | expectancy |
| 49 | `eh06n_cool_192` | EH-06N | 48hクールダウン | PASS | 100 | 0.006 | 5.9 | 48.0 | 0.1 | — |
| 50 | `eh06n_win_20d` | EH-06N | 基準窓20日 | FAIL | 170 | -0.262 | 16.7 | 38.2 | 0.2 | expectancy |
| 51 | `eh06n_win_45d` | EH-06N | 基準窓45日 | FAIL | 139 | -0.260 | 13.0 | 38.1 | 0.0 | expectancy |
| 52 | `eh06n_stop_2p0` | EH-06N | 損切2.0ATR | FAIL | 143 | -0.032 | 9.0 | 51.7 | 0.1 | expectancy |
| 53 | `eh06n_tp_3atr` | EH-06N | 利確3ATR | FAIL | 137 | -0.140 | 8.1 | 32.8 | 0.3 | expectancy |
| 54 | `eh06n_ctrl_follow_retail` | EH-06N | 対照: 個人側に付く | FAIL | 153 | -0.259 | 14.3 | 39.2 | -0.2 | expectancy |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-06N

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh06n_ctrl_follow_retail` | 153 | -0.259 | 14.3 |

n≥30で最良EV: `eh06n_cool_192` EV=0.006 n=100

### EH-06R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06r_base` | 1187 | -0.120 | 51.0 |
| 対照 | `eh06r_ctrl_follow_retail` | 1220 | -0.132 | 54.6 |

本命−対照のEV差: `eh06r_ctrl_follow_retail` 比 +0.013

n≥30で最良EV: `eh06r_cool96_thr2` EV=-0.043 n=148

### EH-09R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09r_base` | 538 | -0.074 | 14.9 |
| 対照 | `eh09r_ctrl_confirm` | 682 | -0.139 | 33.2 |

本命−対照のEV差: `eh09r_ctrl_confirm` 比 +0.065

n≥30で最良EV: `eh09r_perp_vol_slope` EV=-0.006 n=306

## PASS一覧

- `eh06n_cool_192` (EH-06N) EV=0.006 n=100 DD=5.9%
