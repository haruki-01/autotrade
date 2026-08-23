# EH-01〜EH-10 — 検証100サイクル（Set B）

実行UTC: 2026-08-23T05:25:40Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **14 / 54**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh06r_base` | EH-06R | 再掲: 乖離1.0σで即入り | FAIL | 809 | -0.100 | 31.6 | 43.8 | 2.5 | expectancy,drawdown |
| 2 | `eh06r_ctrl_follow_retail` | EH-06R | 対照: 個人側に付く | FAIL | 787 | -0.161 | 46.1 | 40.7 | -2.4 | expectancy,drawdown |
| 3 | `eh06r_cool_96` | EH-06R | 24hクールダウン | FAIL | 247 | -0.140 | 13.2 | 42.1 | 0.5 | expectancy |
| 4 | `eh06r_cool_192` | EH-06R | 48hクールダウン | FAIL | 144 | -0.226 | 11.6 | 41.0 | 0.4 | expectancy |
| 5 | `eh06r_cool_32` | EH-06R | 8hクールダウン | FAIL | 410 | -0.098 | 20.8 | 43.2 | 1.7 | expectancy,drawdown |
| 6 | `eh06r_persist_8` | EH-06R | 乖離が2h続いてから | FAIL | 705 | -0.092 | 27.2 | 44.5 | 2.1 | expectancy,drawdown |
| 7 | `eh06r_persist_32` | EH-06R | 乖離が8h続いてから | FAIL | 566 | -0.089 | 23.8 | 44.0 | 1.8 | expectancy,drawdown |
| 8 | `eh06r_both_extreme` | EH-06R | 個人・上位の両方が偏っている | FAIL | 541 | -0.133 | 28.0 | 42.7 | 1.8 | expectancy,drawdown |
| 9 | `eh06r_thr_2p0` | EH-06R | 乖離2.0σ | FAIL | 358 | -0.087 | 16.2 | 44.7 | 1.5 | expectancy |
| 10 | `eh06r_gate_break` | EH-06R | 12h突破のゲートとして使う | FAIL | 286 | -0.185 | 18.7 | 40.9 | 1.1 | expectancy |
| 11 | `eh06r_gate_break_ctrl` | EH-06R | 対照: ゲートなしの突破 | FAIL | 842 | -0.121 | 34.9 | 43.6 | 1.7 | expectancy,drawdown |
| 12 | `eh06r_gate_break_96` | EH-06R | 24h突破のゲート | FAIL | 217 | -0.220 | 15.9 | 39.6 | 0.6 | expectancy |
| 13 | `eh06r_struct_exit` | EH-06R | 構造退出のみ（目標なし） | FAIL | 554 | -0.095 | 21.9 | 18.1 | 3.1 | expectancy,drawdown |
| 14 | `eh06r_trail_4` | EH-06R | トレール4ATR | FAIL | 298 | -0.061 | 13.2 | 22.8 | 3.4 | expectancy |
| 15 | `eh06r_tp_4atr` | EH-06R | 利確4ATR | FAIL | 434 | -0.108 | 18.6 | 26.5 | 2.7 | expectancy |
| 16 | `eh06r_stop_2p5` | EH-06R | 損切2.5ATR | FAIL | 493 | -0.120 | 23.2 | 55.6 | 2.0 | expectancy,drawdown |
| 17 | `eh06r_win_10d` | EH-06R | 基準窓10日 | FAIL | 721 | -0.045 | 19.2 | 46.5 | 1.6 | expectancy |
| 18 | `eh06r_count_ratio` | EH-06R | 上位比=口座数版 | FAIL | 10 | 0.690 | 2.0 | 60.0 | 0.1 | min_trades |
| 19 | `eh06r_cool96_struct` | EH-06R | 24hクールダウン+構造退出 | FAIL | 214 | -0.079 | 9.8 | 25.2 | 2.1 | expectancy |
| 20 | `eh06r_cool96_thr2` | EH-06R | 24hクールダウン+乖離2.0σ | PASS | 112 | 0.185 | 5.7 | 53.6 | 1.1 | — |
| 21 | `eh09r_base` | EH-09R | 再掲: metrics成行比の傾き | FAIL | 311 | -0.040 | 9.2 | 44.7 | -0.7 | expectancy |
| 22 | `eh09r_ctrl_confirm` | EH-09R | 対照: 成行と同方向（順張り） | FAIL | 443 | -0.160 | 24.9 | 43.1 | 0.9 | expectancy,drawdown |
| 23 | `eh09r_perp_vol` | EH-09R | 先物出来高から成行比を作る | PASS | 262 | 0.036 | 6.1 | 47.7 | -0.7 | — |
| 24 | `eh09r_perp_vol_w32` | EH-09R | 出来高版+計測8h | FAIL | 257 | -0.027 | 9.8 | 44.4 | -0.8 | expectancy |
| 25 | `eh09r_perp_vol_slope` | EH-09R | 出来高版+傾き閾値0.05 | PASS | 150 | 0.087 | 3.4 | 47.3 | -0.4 | — |
| 26 | `eh09r_perp_vol_ctrl` | EH-09R | 対照: 出来高版で順張り | FAIL | 475 | -0.157 | 26.3 | 43.2 | 1.0 | expectancy,drawdown |
| 27 | `eh09r_slope_0p05` | EH-09R | 傾き閾値0.05 | PASS | 179 | 0.057 | 3.7 | 46.9 | -0.2 | — |
| 28 | `eh09r_struct_exit` | EH-09R | 構造退出のみ（目標なし） | FAIL | 349 | -0.001 | 11.0 | 19.8 | -0.6 | expectancy |
| 29 | `eh09r_trail_4` | EH-09R | トレール4ATR | PASS | 193 | 0.415 | 7.3 | 30.1 | -0.2 | — |
| 30 | `eh09r_tp_4atr` | EH-09R | 利確4ATR | FAIL | 272 | -0.053 | 9.6 | 29.0 | -0.6 | expectancy |
| 31 | `eh09r_stop_2p5` | EH-09R | 損切2.5ATR | FAIL | 249 | -0.079 | 12.9 | 55.8 | -1.2 | expectancy |
| 32 | `eh09r_extend_0p5` | EH-09R | 高値を0.5ATR超えてから | FAIL | 139 | -0.054 | 5.3 | 43.2 | -0.3 | expectancy |
| 33 | `eh09r_extend_1p0` | EH-09R | 高値を1.0ATR超えてから | FAIL | 52 | -0.084 | 2.8 | 38.5 | -0.1 | expectancy,min_trades |
| 34 | `eh09r_cool_96` | EH-09R | 24hクールダウン | FAIL | 166 | -0.005 | 4.2 | 48.2 | -0.3 | expectancy |
| 35 | `eh09r_cool_32` | EH-09R | 8hクールダウン | FAIL | 220 | -0.060 | 8.2 | 45.0 | -0.4 | expectancy |
| 36 | `eh09r_persist_8` | EH-09R | 減衰が2h続いてから | PASS | 141 | 0.185 | 2.3 | 52.5 | -0.4 | — |
| 37 | `eh09r_short_only` | EH-09R | ショートのみ | FAIL | 192 | -0.187 | 13.6 | 39.1 | -1.4 | expectancy |
| 38 | `eh09r_slope05_struct` | EH-09R | 傾き0.05+構造退出 | PASS | 201 | 0.051 | 7.3 | 19.9 | -0.6 | — |
| 39 | `eh09r_perpvol_struct` | EH-09R | 出来高版+構造退出 | FAIL | 308 | -0.008 | 10.8 | 19.5 | -0.4 | expectancy |
| 40 | `eh09r_slope05_cool96` | EH-09R | 傾き0.05+24hクールダウン | PASS | 118 | 0.072 | 3.8 | 49.2 | -0.1 | — |
| 41 | `eh06n_center` | EH-06N | 中心: 乖離2.0σ + 24hクールダウン | PASS | 112 | 0.185 | 5.7 | 53.6 | 1.1 | — |
| 42 | `eh06n_thr_1p5` | EH-06N | 乖離1.5σ | FAIL | 169 | -0.164 | 13.5 | 41.4 | 1.0 | expectancy |
| 43 | `eh06n_thr_1p75` | EH-06N | 乖離1.75σ | FAIL | 132 | -0.053 | 8.6 | 43.9 | 1.0 | expectancy |
| 44 | `eh06n_thr_2p25` | EH-06N | 乖離2.25σ | FAIL | 90 | 0.067 | 4.3 | 51.1 | 1.0 | min_trades |
| 45 | `eh06n_thr_2p5` | EH-06N | 乖離2.5σ | FAIL | 67 | 0.307 | 2.2 | 56.7 | 1.1 | min_trades |
| 46 | `eh06n_cool_48` | EH-06N | 12hクールダウン | PASS | 154 | 0.085 | 8.3 | 50.6 | 1.3 | — |
| 47 | `eh06n_cool_64` | EH-06N | 16hクールダウン | PASS | 138 | 0.164 | 2.6 | 54.3 | 1.3 | — |
| 48 | `eh06n_cool_128` | EH-06N | 32hクールダウン | FAIL | 86 | 0.106 | 2.7 | 51.2 | 1.0 | min_trades |
| 49 | `eh06n_cool_192` | EH-06N | 48hクールダウン | FAIL | 73 | 0.269 | 2.7 | 57.5 | 0.9 | min_trades |
| 50 | `eh06n_win_20d` | EH-06N | 基準窓20日 | FAIL | 104 | -0.153 | 7.0 | 43.3 | 0.5 | expectancy |
| 51 | `eh06n_win_45d` | EH-06N | 基準窓45日 | PASS | 108 | 0.026 | 7.1 | 45.4 | 1.5 | — |
| 52 | `eh06n_stop_2p0` | EH-06N | 損切2.0ATR | PASS | 111 | 0.081 | 7.7 | 57.7 | 0.9 | — |
| 53 | `eh06n_tp_3atr` | EH-06N | 利確3ATR | PASS | 100 | 0.217 | 3.7 | 41.0 | 1.3 | — |
| 54 | `eh06n_ctrl_follow_retail` | EH-06N | 対照: 個人側に付く | FAIL | 114 | -0.292 | 12.0 | 36.8 | -0.7 | expectancy |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-06N

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh06n_ctrl_follow_retail` | 114 | -0.292 | 12.0 |

n≥30で最良EV: `eh06n_thr_2p5` EV=0.307 n=67

### EH-06R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06r_base` | 809 | -0.100 | 31.6 |
| 対照 | `eh06r_ctrl_follow_retail` | 787 | -0.161 | 46.1 |

本命−対照のEV差: `eh06r_ctrl_follow_retail` 比 +0.061

n≥30で最良EV: `eh06r_cool96_thr2` EV=0.185 n=112

### EH-09R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09r_base` | 311 | -0.040 | 9.2 |
| 対照 | `eh09r_ctrl_confirm` | 443 | -0.160 | 24.9 |

本命−対照のEV差: `eh09r_ctrl_confirm` 比 +0.121

n≥30で最良EV: `eh09r_trail_4` EV=0.415 n=193

## PASS一覧

- `eh09r_trail_4` (EH-09R) EV=0.415 n=193 DD=7.3%
- `eh06n_tp_3atr` (EH-06N) EV=0.217 n=100 DD=3.7%
- `eh09r_persist_8` (EH-09R) EV=0.185 n=141 DD=2.3%
- `eh06r_cool96_thr2` (EH-06R) EV=0.185 n=112 DD=5.7%
- `eh06n_center` (EH-06N) EV=0.185 n=112 DD=5.7%
- `eh06n_cool_64` (EH-06N) EV=0.164 n=138 DD=2.6%
- `eh09r_perp_vol_slope` (EH-09R) EV=0.087 n=150 DD=3.4%
- `eh06n_cool_48` (EH-06N) EV=0.085 n=154 DD=8.3%
- `eh06n_stop_2p0` (EH-06N) EV=0.081 n=111 DD=7.7%
- `eh09r_slope05_cool96` (EH-09R) EV=0.072 n=118 DD=3.8%
- `eh09r_slope_0p05` (EH-09R) EV=0.057 n=179 DD=3.7%
- `eh09r_slope05_struct` (EH-09R) EV=0.051 n=201 DD=7.3%
- `eh09r_perp_vol` (EH-09R) EV=0.036 n=262 DD=6.1%
- `eh06n_win_45d` (EH-06N) EV=0.026 n=108 DD=7.1%
