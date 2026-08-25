# EH-01〜EH-10 — 検証100サイクル（Set A）

実行UTC: 2026-08-23T05:24:00Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **11 / 54**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh06r_base` | EH-06R | 再掲: 乖離1.0σで即入り | FAIL | 917 | -0.069 | 26.3 | 44.5 | 0.6 | expectancy,drawdown |
| 2 | `eh06r_ctrl_follow_retail` | EH-06R | 対照: 個人側に付く | FAIL | 851 | -0.204 | 57.8 | 39.1 | -0.8 | expectancy,drawdown |
| 3 | `eh06r_cool_96` | EH-06R | 24hクールダウン | FAIL | 246 | -0.068 | 8.1 | 41.9 | 0.4 | expectancy |
| 4 | `eh06r_cool_192` | EH-06R | 48hクールダウン | FAIL | 148 | -0.190 | 10.6 | 37.2 | 0.5 | expectancy |
| 5 | `eh06r_cool_32` | EH-06R | 8hクールダウン | FAIL | 399 | -0.009 | 7.4 | 46.6 | 0.4 | expectancy |
| 6 | `eh06r_persist_8` | EH-06R | 乖離が2h続いてから | FAIL | 826 | -0.063 | 22.5 | 44.6 | 0.6 | expectancy,drawdown |
| 7 | `eh06r_persist_32` | EH-06R | 乖離が8h続いてから | FAIL | 741 | -0.080 | 25.1 | 44.3 | 0.6 | expectancy,drawdown |
| 8 | `eh06r_both_extreme` | EH-06R | 個人・上位の両方が偏っている | FAIL | 752 | -0.085 | 26.2 | 43.8 | 0.9 | expectancy,drawdown |
| 9 | `eh06r_thr_2p0` | EH-06R | 乖離2.0σ | FAIL | 468 | -0.059 | 16.6 | 43.8 | 0.5 | expectancy |
| 10 | `eh06r_gate_break` | EH-06R | 12h突破のゲートとして使う | FAIL | 300 | -0.070 | 11.1 | 46.3 | 0.2 | expectancy |
| 11 | `eh06r_gate_break_ctrl` | EH-06R | 対照: ゲートなしの突破 | FAIL | 789 | -0.086 | 24.6 | 45.6 | 0.3 | expectancy,drawdown |
| 12 | `eh06r_gate_break_96` | EH-06R | 24h突破のゲート | FAIL | 216 | -0.090 | 11.1 | 45.4 | 0.1 | expectancy |
| 13 | `eh06r_struct_exit` | EH-06R | 構造退出のみ（目標なし） | PASS | 462 | 0.016 | 14.0 | 21.4 | 0.7 | — |
| 14 | `eh06r_trail_4` | EH-06R | トレール4ATR | PASS | 345 | 0.000 | 13.7 | 27.0 | 0.9 | — |
| 15 | `eh06r_tp_4atr` | EH-06R | 利確4ATR | FAIL | 425 | -0.026 | 14.2 | 29.9 | 1.0 | expectancy |
| 16 | `eh06r_stop_2p5` | EH-06R | 損切2.5ATR | FAIL | 588 | -0.058 | 22.2 | 56.1 | 0.5 | expectancy,drawdown |
| 17 | `eh06r_win_10d` | EH-06R | 基準窓10日 | FAIL | 942 | -0.076 | 34.5 | 43.8 | 0.2 | expectancy,drawdown |
| 18 | `eh06r_count_ratio` | EH-06R | 上位比=口座数版 | FAIL | 13 | -0.615 | 2.7 | 23.1 | 0.0 | expectancy,min_trades |
| 19 | `eh06r_cool96_struct` | EH-06R | 24hクールダウン+構造退出 | PASS | 199 | 0.133 | 7.3 | 23.1 | 1.0 | — |
| 20 | `eh06r_cool96_thr2` | EH-06R | 24hクールダウン+乖離2.0σ | PASS | 150 | 0.045 | 2.9 | 48.0 | 0.3 | — |
| 21 | `eh09r_base` | EH-09R | 再掲: metrics成行比の傾き | FAIL | 239 | -0.165 | 14.0 | 42.7 | -0.3 | expectancy |
| 22 | `eh09r_ctrl_confirm` | EH-09R | 対照: 成行と同方向（順張り） | FAIL | 341 | -0.115 | 14.6 | 45.7 | 0.1 | expectancy |
| 23 | `eh09r_perp_vol` | EH-09R | 先物出来高から成行比を作る | FAIL | 171 | -0.187 | 11.4 | 40.4 | -0.3 | expectancy |
| 24 | `eh09r_perp_vol_w32` | EH-09R | 出来高版+計測8h | FAIL | 211 | -0.089 | 8.1 | 46.4 | -0.0 | expectancy |
| 25 | `eh09r_perp_vol_slope` | EH-09R | 出来高版+傾き閾値0.05 | FAIL | 92 | -0.169 | 6.4 | 42.4 | -0.1 | expectancy,min_trades |
| 26 | `eh09r_perp_vol_ctrl` | EH-09R | 対照: 出来高版で順張り | FAIL | 401 | -0.107 | 15.9 | 44.4 | -0.0 | expectancy |
| 27 | `eh09r_slope_0p05` | EH-09R | 傾き閾値0.05 | FAIL | 131 | -0.086 | 4.6 | 46.6 | -0.2 | expectancy |
| 28 | `eh09r_struct_exit` | EH-09R | 構造退出のみ（目標なし） | FAIL | 264 | -0.159 | 16.2 | 20.8 | -0.9 | expectancy |
| 29 | `eh09r_trail_4` | EH-09R | トレール4ATR | FAIL | 191 | -0.171 | 13.3 | 23.0 | -1.1 | expectancy |
| 30 | `eh09r_tp_4atr` | EH-09R | 利確4ATR | FAIL | 221 | -0.150 | 13.0 | 27.6 | -1.1 | expectancy |
| 31 | `eh09r_stop_2p5` | EH-09R | 損切2.5ATR | FAIL | 211 | -0.201 | 15.8 | 52.6 | -0.4 | expectancy |
| 32 | `eh09r_extend_0p5` | EH-09R | 高値を0.5ATR超えてから | FAIL | 114 | -0.245 | 9.4 | 39.5 | -0.1 | expectancy |
| 33 | `eh09r_extend_1p0` | EH-09R | 高値を1.0ATR超えてから | FAIL | 46 | -0.208 | 4.0 | 41.3 | -0.1 | expectancy,min_trades |
| 34 | `eh09r_cool_96` | EH-09R | 24hクールダウン | FAIL | 143 | -0.128 | 6.9 | 44.8 | -0.2 | expectancy |
| 35 | `eh09r_cool_32` | EH-09R | 8hクールダウン | FAIL | 175 | -0.185 | 11.7 | 42.3 | -0.2 | expectancy |
| 36 | `eh09r_persist_8` | EH-09R | 減衰が2h続いてから | FAIL | 116 | -0.134 | 5.7 | 43.1 | -0.1 | expectancy |
| 37 | `eh09r_short_only` | EH-09R | ショートのみ | FAIL | 176 | -0.211 | 13.3 | 40.3 | -0.6 | expectancy |
| 38 | `eh09r_slope05_struct` | EH-09R | 傾き0.05+構造退出 | FAIL | 148 | -0.165 | 8.4 | 20.9 | -0.7 | expectancy |
| 39 | `eh09r_perpvol_struct` | EH-09R | 出来高版+構造退出 | FAIL | 196 | -0.139 | 11.8 | 19.9 | -0.7 | expectancy |
| 40 | `eh09r_slope05_cool96` | EH-09R | 傾き0.05+24hクールダウン | FAIL | 93 | -0.101 | 3.6 | 45.2 | -0.2 | expectancy,min_trades |
| 41 | `eh06n_center` | EH-06N | 中心: 乖離2.0σ + 24hクールダウン | PASS | 150 | 0.045 | 2.9 | 48.0 | 0.3 | — |
| 42 | `eh06n_thr_1p5` | EH-06N | 乖離1.5σ | FAIL | 190 | -0.018 | 4.6 | 44.7 | 0.6 | expectancy |
| 43 | `eh06n_thr_1p75` | EH-06N | 乖離1.75σ | PASS | 168 | 0.022 | 3.5 | 47.0 | 0.3 | — |
| 44 | `eh06n_thr_2p25` | EH-06N | 乖離2.25σ | PASS | 131 | 0.091 | 3.3 | 49.6 | 0.3 | — |
| 45 | `eh06n_thr_2p5` | EH-06N | 乖離2.5σ | PASS | 115 | 0.134 | 2.9 | 53.9 | 0.3 | — |
| 46 | `eh06n_cool_48` | EH-06N | 12hクールダウン | FAIL | 200 | -0.000 | 5.2 | 46.5 | 0.3 | expectancy |
| 47 | `eh06n_cool_64` | EH-06N | 16hクールダウン | FAIL | 185 | -0.002 | 5.1 | 46.5 | 0.5 | expectancy |
| 48 | `eh06n_cool_128` | EH-06N | 32hクールダウン | PASS | 125 | 0.044 | 2.9 | 45.6 | 0.3 | — |
| 49 | `eh06n_cool_192` | EH-06N | 48hクールダウン | FAIL | 92 | 0.014 | 4.8 | 46.7 | 0.3 | min_trades |
| 50 | `eh06n_win_20d` | EH-06N | 基準窓20日 | FAIL | 162 | -0.055 | 5.4 | 45.7 | 0.2 | expectancy |
| 51 | `eh06n_win_45d` | EH-06N | 基準窓45日 | PASS | 144 | 0.093 | 3.6 | 52.1 | 0.5 | — |
| 52 | `eh06n_stop_2p0` | EH-06N | 損切2.0ATR | FAIL | 140 | -0.002 | 4.1 | 51.4 | 0.3 | expectancy |
| 53 | `eh06n_tp_3atr` | EH-06N | 利確3ATR | PASS | 133 | 0.045 | 4.0 | 38.3 | 0.5 | — |
| 54 | `eh06n_ctrl_follow_retail` | EH-06N | 対照: 個人側に付く | FAIL | 144 | -0.254 | 14.3 | 38.9 | -0.4 | expectancy |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-06N

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh06n_ctrl_follow_retail` | 144 | -0.254 | 14.3 |

n≥30で最良EV: `eh06n_thr_2p5` EV=0.134 n=115

### EH-06R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06r_base` | 917 | -0.069 | 26.3 |
| 対照 | `eh06r_ctrl_follow_retail` | 851 | -0.204 | 57.8 |

本命−対照のEV差: `eh06r_ctrl_follow_retail` 比 +0.134

n≥30で最良EV: `eh06r_cool96_struct` EV=0.133 n=199

### EH-09R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09r_base` | 239 | -0.165 | 14.0 |
| 対照 | `eh09r_ctrl_confirm` | 341 | -0.115 | 14.6 |

本命−対照のEV差: `eh09r_ctrl_confirm` 比 -0.050

n≥30で最良EV: `eh09r_slope_0p05` EV=-0.086 n=131

## PASS一覧

- `eh06n_thr_2p5` (EH-06N) EV=0.134 n=115 DD=2.9%
- `eh06r_cool96_struct` (EH-06R) EV=0.133 n=199 DD=7.3%
- `eh06n_win_45d` (EH-06N) EV=0.093 n=144 DD=3.6%
- `eh06n_thr_2p25` (EH-06N) EV=0.091 n=131 DD=3.3%
- `eh06r_cool96_thr2` (EH-06R) EV=0.045 n=150 DD=2.9%
- `eh06n_center` (EH-06N) EV=0.045 n=150 DD=2.9%
- `eh06n_tp_3atr` (EH-06N) EV=0.045 n=133 DD=4.0%
- `eh06n_cool_128` (EH-06N) EV=0.044 n=125 DD=2.9%
- `eh06n_thr_1p75` (EH-06N) EV=0.022 n=168 DD=3.5%
- `eh06r_struct_exit` (EH-06R) EV=0.016 n=462 DD=14.0%
- `eh06r_trail_4` (EH-06R) EV=0.000 n=345 DD=13.7%
