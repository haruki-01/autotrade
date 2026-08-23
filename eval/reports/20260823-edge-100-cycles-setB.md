# EH-01〜EH-10 — 検証100サイクル（Set B）

実行UTC: 2026-08-23T02:30:57Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **11 / 100**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh01_base` | EH-01 | 24h突破+OI増0.5%/4h | FAIL | 235 | -0.097 | 16.1 | 26.4 | 1.4 | expectancy |
| 2 | `eh01_ctrl_no_oi` | EH-01 | 対照: OIフィルタなし | FAIL | 377 | -0.151 | 26.8 | 28.1 | 1.3 | expectancy,drawdown |
| 3 | `eh01_ctrl_oi_down` | EH-01 | 対照: OI減の突破 | FAIL | 171 | -0.233 | 17.6 | 26.9 | 0.5 | expectancy |
| 4 | `eh01_thr_1p0` | EH-01 | OI閾値1.0% | FAIL | 180 | -0.029 | 10.5 | 28.3 | 1.4 | expectancy |
| 5 | `eh01_thr_0p2` | EH-01 | OI閾値0.2% | FAIL | 257 | -0.083 | 15.9 | 26.5 | 1.5 | expectancy |
| 6 | `eh01_oiwin_4` | EH-01 | OI計測1h | FAIL | 194 | -0.152 | 16.5 | 23.7 | 1.4 | expectancy |
| 7 | `eh01_oiwin_32` | EH-01 | OI計測8h | FAIL | 239 | -0.128 | 19.1 | 25.5 | 1.4 | expectancy |
| 8 | `eh01_brk_48` | EH-01 | 突破12h | FAIL | 323 | -0.085 | 16.0 | 28.5 | 1.5 | expectancy |
| 9 | `eh01_brk_192` | EH-01 | 突破48h | PASS | 157 | 0.010 | 9.6 | 30.6 | 1.4 | — |
| 10 | `eh01_long_only` | EH-01 | ロングのみ | PASS | 138 | 0.126 | 5.2 | 31.2 | 2.3 | — |
| 11 | `eh02_base` | EH-02 | 現物先行1h+0.05% | FAIL | 39 | 0.291 | 4.1 | 51.3 | 1.1 | min_trades |
| 12 | `eh02_ctrl_no_lead` | EH-02 | 対照: 乖離なし | FAIL | 1237 | -0.065 | 48.7 | 43.9 | 2.2 | expectancy,drawdown |
| 13 | `eh02_ctrl_perp_lead` | EH-02 | 対照: 先物先行 | FAIL | 76 | -0.259 | 10.8 | 38.2 | 0.5 | expectancy,min_trades |
| 14 | `eh02_thr_0p10` | EH-02 | 閾値0.10% | FAIL | 8 | 0.339 | 0.9 | 50.0 | -0.4 | min_trades |
| 15 | `eh02_thr_0p02` | EH-02 | 閾値0.02% | FAIL | 628 | -0.041 | 22.4 | 44.4 | 0.8 | expectancy,drawdown |
| 16 | `eh02_win_2` | EH-02 | 計測30分 | FAIL | 36 | 0.123 | 2.9 | 47.2 | 0.4 | min_trades |
| 17 | `eh02_win_8` | EH-02 | 計測2h | FAIL | 55 | 0.327 | 4.3 | 56.4 | 1.6 | min_trades |
| 18 | `eh02_no_mom` | EH-02 | 同方向確認なし | FAIL | 93 | 0.056 | 6.2 | 45.2 | 0.0 | min_trades |
| 19 | `eh02_trail_1p5` | EH-02 | トレール1.5ATR | FAIL | 43 | 0.142 | 2.9 | 46.5 | 0.4 | min_trades |
| 20 | `eh02_long_only` | EH-02 | ロングのみ | FAIL | 28 | 0.351 | 3.3 | 57.1 | 1.2 | min_trades |
| 21 | `eh03_base` | EH-03 | プレミアム上位10%+失速 | FAIL | 346 | -0.280 | 39.1 | 35.8 | -5.0 | expectancy,drawdown |
| 22 | `eh03_both_sides` | EH-03 | 両側 | FAIL | 687 | -0.148 | 46.3 | 40.2 | -2.2 | expectancy,drawdown |
| 23 | `eh03_ctrl_no_stall` | EH-03 | 対照: 失速確認なし | FAIL | 361 | -0.280 | 41.0 | 36.0 | -5.1 | expectancy,drawdown |
| 24 | `eh03_rank_0p95` | EH-03 | 上位5% | FAIL | 231 | -0.330 | 30.3 | 34.6 | -3.6 | expectancy,drawdown |
| 25 | `eh03_rank_0p80` | EH-03 | 上位20% | FAIL | 468 | -0.192 | 38.8 | 38.5 | -5.9 | expectancy,drawdown |
| 26 | `eh03_win_10d` | EH-03 | ランク窓10日 | FAIL | 402 | -0.240 | 39.5 | 37.6 | -5.2 | expectancy,drawdown |
| 27 | `eh03_win_60d` | EH-03 | ランク窓60日 | FAIL | 301 | -0.234 | 30.7 | 38.2 | -4.8 | expectancy,drawdown |
| 28 | `eh03_stall_24` | EH-03 | 失速6h | FAIL | 344 | -0.277 | 38.6 | 36.0 | -5.0 | expectancy,drawdown |
| 29 | `eh03_tp_3atr` | EH-03 | 利確3ATR | FAIL | 287 | -0.266 | 33.2 | 29.3 | -5.4 | expectancy,drawdown |
| 30 | `eh03_stop_2p5` | EH-03 | 損切2.5ATR | FAIL | 212 | -0.371 | 30.6 | 45.8 | -4.9 | expectancy,drawdown |
| 31 | `eh04_base` | EH-04 | 4日トレンド+funding安 | FAIL | 898 | -0.080 | 39.1 | 25.1 | -0.9 | expectancy,drawdown |
| 32 | `eh04_ctrl_any` | EH-04 | 対照: fundingフィルタなし | FAIL | 984 | -0.062 | 38.0 | 25.6 | 3.0 | expectancy,drawdown |
| 33 | `eh04_ctrl_expensive` | EH-04 | 対照: funding高 | FAIL | 145 | -0.052 | 9.2 | 26.2 | 4.3 | expectancy |
| 34 | `eh04_thr_0` | EH-04 | 閾値0（受取のみ） | FAIL | 547 | -0.119 | 31.8 | 24.3 | -4.2 | expectancy,drawdown |
| 35 | `eh04_thr_0p03` | EH-04 | 閾値0.03% | FAIL | 952 | -0.060 | 35.8 | 25.4 | 0.9 | expectancy,drawdown |
| 36 | `eh04_trend_2d` | EH-04 | トレンド2日 | FAIL | 821 | -0.097 | 41.1 | 26.8 | -1.6 | expectancy,drawdown |
| 37 | `eh04_trend_10d` | EH-04 | トレンド10日 | FAIL | 933 | -0.089 | 43.6 | 23.6 | -0.2 | expectancy,drawdown |
| 38 | `eh04_exit_24` | EH-04 | 構造退出24h | FAIL | 721 | -0.068 | 29.5 | 28.6 | -0.8 | expectancy,drawdown |
| 39 | `eh04_trail_4` | EH-04 | トレール4ATR | FAIL | 711 | -0.033 | 22.2 | 21.0 | -0.8 | expectancy,drawdown |
| 40 | `eh04_long_only` | EH-04 | ロングのみ | FAIL | 433 | -0.014 | 13.1 | 26.3 | 3.4 | expectancy |
| 41 | `eh05_base` | EH-05 | OI上位10%+高値更新失敗 | FAIL | 84 | -0.248 | 8.5 | 32.1 | -0.8 | expectancy,min_trades |
| 42 | `eh05_both_sides` | EH-05 | 両側 | FAIL | 130 | -0.135 | 8.2 | 39.2 | -0.4 | expectancy |
| 43 | `eh05_ctrl_no_oi` | EH-05 | 対照: OI条件なし | FAIL | 312 | -0.172 | 23.5 | 37.8 | -4.2 | expectancy,drawdown |
| 44 | `eh05_ctrl_no_tt` | EH-05 | 対照: 上位比なし | FAIL | 173 | -0.134 | 11.3 | 38.7 | -1.4 | expectancy |
| 45 | `eh05_rank_0p95` | EH-05 | OI上位5% | FAIL | 65 | -0.126 | 3.8 | 38.5 | -0.6 | expectancy,min_trades |
| 46 | `eh05_rank_0p80` | EH-05 | OI上位20% | FAIL | 113 | -0.238 | 11.4 | 33.6 | -1.0 | expectancy |
| 47 | `eh05_win_10d` | EH-05 | OIランク窓10日 | FAIL | 88 | -0.134 | 6.6 | 37.5 | -0.9 | expectancy,min_trades |
| 48 | `eh05_stall_24` | EH-05 | 失速6h | FAIL | 87 | -0.224 | 8.2 | 33.3 | -0.8 | expectancy,min_trades |
| 49 | `eh05_count_ratio` | EH-05 | 上位比=口座数版 | FAIL | 29 | -0.172 | 3.6 | 34.5 | -0.3 | expectancy,min_trades |
| 50 | `eh05_tp_3atr` | EH-05 | 利確3ATR | FAIL | 73 | -0.252 | 7.7 | 24.7 | -1.0 | expectancy,min_trades |
| 51 | `eh06_base` | EH-06 | 個人-上位 乖離1.0σ | FAIL | 809 | -0.051 | 31.6 | 43.8 | 2.5 | expectancy,drawdown |
| 52 | `eh06_ctrl_follow_retail` | EH-06 | 対照: 個人側に付く | FAIL | 787 | -0.112 | 46.1 | 40.7 | -2.4 | expectancy,drawdown |
| 53 | `eh06_thr_1p5` | EH-06 | 乖離1.5σ | FAIL | 513 | -0.069 | 24.3 | 43.1 | 1.8 | expectancy,drawdown |
| 54 | `eh06_thr_0p5` | EH-06 | 乖離0.5σ | FAIL | 1090 | -0.028 | 29.8 | 45.0 | 2.7 | expectancy,drawdown |
| 55 | `eh06_win_10d` | EH-06 | 基準窓10日 | PASS | 721 | 0.004 | 19.2 | 46.5 | 1.6 | — |
| 56 | `eh06_win_60d` | EH-06 | 基準窓60日 | FAIL | 769 | -0.019 | 24.5 | 46.2 | 4.2 | expectancy,drawdown |
| 57 | `eh06_count_ratio` | EH-06 | 上位比=口座数版 | FAIL | 10 | 0.739 | 2.0 | 60.0 | 0.1 | min_trades |
| 58 | `eh06_tp_3atr` | EH-06 | 利確3ATR | FAIL | 548 | -0.028 | 18.6 | 33.9 | 2.7 | expectancy |
| 59 | `eh06_stop_2p5` | EH-06 | 損切2.5ATR | FAIL | 493 | -0.071 | 23.2 | 55.6 | 2.0 | expectancy,drawdown |
| 60 | `eh06_short_only` | EH-06 | ショートのみ | FAIL | 369 | -0.059 | 17.4 | 43.1 | -2.5 | expectancy |
| 61 | `eh07_base` | EH-07 | OI急減1%/2h+大足 | FAIL | 62 | -0.073 | 6.6 | 40.3 | 0.0 | expectancy,min_trades |
| 62 | `eh07_ctrl_fade` | EH-07 | 対照: ショックをフェード | FAIL | 62 | -0.144 | 6.1 | 37.1 | 0.4 | expectancy,min_trades |
| 63 | `eh07_thr_2p0` | EH-07 | OI急減2% | FAIL | 31 | -0.074 | 4.3 | 45.2 | -0.0 | expectancy,min_trades |
| 64 | `eh07_thr_0p5` | EH-07 | OI急減0.5% | FAIL | 92 | -0.077 | 8.0 | 41.3 | 0.2 | expectancy,min_trades |
| 65 | `eh07_range_3` | EH-07 | 値幅3ATR | FAIL | 18 | 0.013 | 1.9 | 44.4 | 0.0 | min_trades |
| 66 | `eh07_range_1p5` | EH-07 | 値幅1.5ATR | FAIL | 131 | -0.146 | 11.6 | 40.5 | 0.2 | expectancy |
| 67 | `eh07_delay_0` | EH-07 | 遅延なし | FAIL | 69 | -0.129 | 6.1 | 43.5 | 0.1 | expectancy,min_trades |
| 68 | `eh07_delay_8` | EH-07 | 遅延2h | FAIL | 57 | 0.056 | 5.6 | 45.6 | 0.6 | min_trades |
| 69 | `eh07_pre_48h` | EH-07 | 元方向48h | FAIL | 62 | 0.225 | 3.8 | 51.6 | 0.0 | min_trades |
| 70 | `eh07_flushwin_16` | EH-07 | OI計測4h | FAIL | 69 | 0.086 | 4.3 | 46.4 | 0.2 | min_trades |
| 71 | `eh08_base` | EH-08 | 圧縮+OI増1%/24h | FAIL | 196 | -0.008 | 6.1 | 31.6 | 0.9 | expectancy |
| 72 | `eh08_ctrl_no_build` | EH-08 | 対照: OI増なし | PASS | 269 | 0.050 | 6.5 | 32.7 | 1.3 | — |
| 73 | `eh08_build_2p0` | EH-08 | OI増2% | FAIL | 150 | -0.033 | 5.7 | 28.7 | 0.6 | expectancy |
| 74 | `eh08_build_0p5` | EH-08 | OI増0.5% | FAIL | 220 | -0.043 | 8.9 | 30.9 | 0.9 | expectancy |
| 75 | `eh08_quiet_0p2` | EH-08 | 圧縮下位20% | FAIL | 143 | -0.045 | 5.5 | 31.5 | 0.7 | expectancy |
| 76 | `eh08_quiet_0p4` | EH-08 | 圧縮下位40% | FAIL | 240 | -0.105 | 13.2 | 28.7 | 0.9 | expectancy |
| 77 | `eh08_win_48` | EH-08 | 圧縮窓12h | FAIL | 271 | -0.019 | 8.2 | 28.4 | 0.6 | expectancy |
| 78 | `eh08_win_192` | EH-08 | 圧縮窓48h | FAIL | 171 | -0.008 | 10.4 | 31.6 | 0.9 | expectancy |
| 79 | `eh08_trail_4` | EH-08 | トレール4ATR | PASS | 182 | 0.007 | 6.1 | 27.5 | 1.1 | — |
| 80 | `eh08_long_only` | EH-08 | ロングのみ | PASS | 105 | 0.054 | 5.1 | 32.4 | 1.7 | — |
| 81 | `eh09_base` | EH-09 | 高値更新+成行買い減衰 | PASS | 311 | 0.010 | 9.2 | 44.7 | -0.7 | — |
| 82 | `eh09_ctrl_confirm` | EH-09 | 対照: 成行と同方向 | FAIL | 443 | -0.111 | 24.9 | 43.1 | 0.9 | expectancy,drawdown |
| 83 | `eh09_win_8` | EH-09 | 成行計測2h | PASS | 302 | 0.032 | 11.3 | 44.7 | -0.7 | — |
| 84 | `eh09_win_32` | EH-09 | 成行計測8h | PASS | 291 | 0.003 | 11.3 | 43.3 | -1.1 | — |
| 85 | `eh09_slope_0p05` | EH-09 | 傾き閾値0.05 | PASS | 179 | 0.106 | 3.7 | 46.9 | -0.2 | — |
| 86 | `eh09_slope_0p15` | EH-09 | 傾き閾値0.15 | FAIL | 49 | 0.062 | 2.5 | 49.0 | -0.1 | min_trades |
| 87 | `eh09_tp_3atr` | EH-09 | 利確3ATR | FAIL | 297 | -0.039 | 11.7 | 33.3 | -0.9 | expectancy |
| 88 | `eh09_stop_2p5` | EH-09 | 損切2.5ATR | FAIL | 249 | -0.030 | 12.9 | 55.8 | -1.2 | expectancy |
| 89 | `eh09_short_only` | EH-09 | ショートのみ | FAIL | 192 | -0.137 | 13.6 | 39.1 | -1.4 | expectancy |
| 90 | `eh09_trail_2p5` | EH-09 | トレール併用 | PASS | 266 | 0.021 | 11.8 | 31.2 | -1.1 | — |
| 91 | `eh10_base` | EH-10 | funding高→平常(≤0.01%)+構造維持 | FAIL | 7 | 1.330 | 0.5 | 57.1 | 0.3 | min_trades |
| 92 | `eh10_ctrl_no_reset` | EH-10 | 対照: リセット条件なし | FAIL | 984 | -0.062 | 38.0 | 25.6 | 3.0 | expectancy,drawdown |
| 93 | `eh10_high_0p05` | EH-10 | 事前高0.05% | FAIL | 1 | 1.812 | 0.0 | 100.0 | 0.0 | min_trades |
| 94 | `eh10_high_0p02` | EH-10 | 事前高0.02% | FAIL | 20 | 0.208 | 1.8 | 35.0 | 0.4 | min_trades |
| 95 | `eh10_now_0p02` | EH-10 | 平常0.02%まで許容 | FAIL | 14 | 0.385 | 1.2 | 35.7 | 0.4 | min_trades |
| 96 | `eh10_win_2d` | EH-10 | 参照窓2日 | FAIL | 17 | 0.573 | 1.2 | 41.2 | 0.4 | min_trades |
| 97 | `eh10_win_5d` | EH-10 | 参照窓5日 | FAIL | 49 | 0.084 | 3.0 | 36.7 | 0.8 | min_trades |
| 98 | `eh10_trend_2d` | EH-10 | トレンド2日 | FAIL | 6 | 1.167 | 0.7 | 50.0 | 0.2 | min_trades |
| 99 | `eh10_trail_4` | EH-10 | トレール4ATR | FAIL | 6 | 1.794 | 0.6 | 66.7 | 0.3 | min_trades |
| 100 | `eh10_long_only` | EH-10 | ロングのみ | FAIL | 7 | 1.330 | 0.5 | 57.1 | 0.3 | min_trades |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-01

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh01_base` | 235 | -0.097 | 16.1 |
| 対照 | `eh01_ctrl_no_oi` | 377 | -0.151 | 26.8 |
| 対照 | `eh01_ctrl_oi_down` | 171 | -0.233 | 17.6 |

本命−対照のEV差: `eh01_ctrl_no_oi` 比 +0.054 / `eh01_ctrl_oi_down` 比 +0.136

n≥30で最良EV: `eh01_long_only` EV=0.126 n=138

### EH-02

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh02_base` | 39 | 0.291 | 4.1 |
| 対照 | `eh02_ctrl_no_lead` | 1237 | -0.065 | 48.7 |
| 対照 | `eh02_ctrl_perp_lead` | 76 | -0.259 | 10.8 |

本命−対照のEV差: `eh02_ctrl_no_lead` 比 +0.355 / `eh02_ctrl_perp_lead` 比 +0.549

n≥30で最良EV: `eh02_win_8` EV=0.327 n=55

### EH-03

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh03_base` | 346 | -0.280 | 39.1 |
| 対照 | `eh03_ctrl_no_stall` | 361 | -0.280 | 41.0 |

本命−対照のEV差: `eh03_ctrl_no_stall` 比 +0.001

n≥30で最良EV: `eh03_both_sides` EV=-0.148 n=687

### EH-04

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh04_base` | 898 | -0.080 | 39.1 |
| 対照 | `eh04_ctrl_any` | 984 | -0.062 | 38.0 |
| 対照 | `eh04_ctrl_expensive` | 145 | -0.052 | 9.2 |

本命−対照のEV差: `eh04_ctrl_any` 比 -0.018 / `eh04_ctrl_expensive` 比 -0.027

n≥30で最良EV: `eh04_long_only` EV=-0.014 n=433

### EH-05

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh05_base` | 84 | -0.248 | 8.5 |
| 対照 | `eh05_ctrl_no_oi` | 312 | -0.172 | 23.5 |
| 対照 | `eh05_ctrl_no_tt` | 173 | -0.134 | 11.3 |

本命−対照のEV差: `eh05_ctrl_no_oi` 比 -0.076 / `eh05_ctrl_no_tt` 比 -0.114

n≥30で最良EV: `eh05_rank_0p95` EV=-0.126 n=65

### EH-06

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06_base` | 809 | -0.051 | 31.6 |
| 対照 | `eh06_ctrl_follow_retail` | 787 | -0.112 | 46.1 |

本命−対照のEV差: `eh06_ctrl_follow_retail` 比 +0.061

n≥30で最良EV: `eh06_win_10d` EV=0.004 n=721

### EH-07

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh07_base` | 62 | -0.073 | 6.6 |
| 対照 | `eh07_ctrl_fade` | 62 | -0.144 | 6.1 |

本命−対照のEV差: `eh07_ctrl_fade` 比 +0.071

n≥30で最良EV: `eh07_pre_48h` EV=0.225 n=62

### EH-08

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh08_base` | 196 | -0.008 | 6.1 |
| 対照 | `eh08_ctrl_no_build` | 269 | 0.050 | 6.5 |

本命−対照のEV差: `eh08_ctrl_no_build` 比 -0.057

n≥30で最良EV: `eh08_long_only` EV=0.054 n=105

### EH-09

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09_base` | 311 | 0.010 | 9.2 |
| 対照 | `eh09_ctrl_confirm` | 443 | -0.111 | 24.9 |

本命−対照のEV差: `eh09_ctrl_confirm` 比 +0.121

n≥30で最良EV: `eh09_slope_0p05` EV=0.106 n=179

### EH-10

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh10_base` | 7 | 1.330 | 0.5 |
| 対照 | `eh10_ctrl_no_reset` | 984 | -0.062 | 38.0 |

本命−対照のEV差: `eh10_ctrl_no_reset` 比 +1.392

n≥30で最良EV: `eh10_win_5d` EV=0.084 n=49

## PASS一覧

- `eh01_long_only` (EH-01) EV=0.126 n=138 DD=5.2%
- `eh09_slope_0p05` (EH-09) EV=0.106 n=179 DD=3.7%
- `eh08_long_only` (EH-08) EV=0.054 n=105 DD=5.1%
- `eh08_ctrl_no_build` (EH-08) EV=0.050 n=269 DD=6.5%
- `eh09_win_8` (EH-09) EV=0.032 n=302 DD=11.3%
- `eh09_trail_2p5` (EH-09) EV=0.021 n=266 DD=11.8%
- `eh01_brk_192` (EH-01) EV=0.010 n=157 DD=9.6%
- `eh09_base` (EH-09) EV=0.010 n=311 DD=9.2%
- `eh08_trail_4` (EH-08) EV=0.007 n=182 DD=6.1%
- `eh06_win_10d` (EH-06) EV=0.004 n=721 DD=19.2%
- `eh09_win_32` (EH-09) EV=0.003 n=291 DD=11.3%
