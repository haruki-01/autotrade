# EH-01〜EH-10 — 検証100サイクル（Set C）

実行UTC: 2026-08-23T02:39:35Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **12 / 95**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh01_base` | EH-01 | 24h突破+OI増0.5%/4h | FAIL | 313 | -0.018 | 11.6 | 30.7 | 0.2 | expectancy |
| 2 | `eh01_ctrl_no_oi` | EH-01 | 対照: OIフィルタなし | FAIL | 614 | -0.099 | 34.5 | 28.5 | 0.2 | expectancy,drawdown |
| 3 | `eh01_ctrl_oi_down` | EH-01 | 対照: OI減の突破 | FAIL | 247 | -0.073 | 13.9 | 30.0 | -0.1 | expectancy |
| 4 | `eh01_thr_1p0` | EH-01 | OI閾値1.0% | FAIL | 240 | -0.055 | 12.9 | 26.2 | 0.1 | expectancy |
| 5 | `eh01_thr_0p2` | EH-01 | OI閾値0.2% | FAIL | 375 | -0.061 | 16.4 | 30.9 | 0.2 | expectancy |
| 6 | `eh01_oiwin_4` | EH-01 | OI計測1h | FAIL | 286 | -0.065 | 15.4 | 31.1 | 0.3 | expectancy |
| 7 | `eh01_oiwin_32` | EH-01 | OI計測8h | FAIL | 335 | -0.069 | 17.5 | 28.1 | 0.3 | expectancy |
| 8 | `eh01_brk_48` | EH-01 | 突破12h | FAIL | 411 | -0.006 | 13.0 | 31.4 | 0.1 | expectancy |
| 9 | `eh01_brk_192` | EH-01 | 突破48h | PASS | 227 | 0.008 | 9.2 | 30.0 | 0.2 | — |
| 10 | `eh01_long_only` | EH-01 | ロングのみ | FAIL | 191 | -0.129 | 14.2 | 28.3 | 0.8 | expectancy |
| 11 | `eh02_base` | EH-02 | 現物先行1h+0.05% | FAIL | 14 | -0.533 | 3.4 | 35.7 | 0.0 | expectancy,min_trades |
| 12 | `eh02_ctrl_no_lead` | — | — | ERR | — | — | — | — | — | TypeError: Object of type complex is not JSON serializable |
| 13 | `eh02_ctrl_perp_lead` | EH-02 | 対照: 先物先行 | FAIL | 16 | -0.952 | 5.3 | 25.0 | 0.1 | expectancy,min_trades |
| 14 | `eh02_thr_0p10` | EH-02 | 閾値0.10% | FAIL | 4 | -0.977 | 1.8 | 25.0 | 0.0 | expectancy,min_trades |
| 15 | `eh02_thr_0p02` | EH-02 | 閾値0.02% | FAIL | 673 | -0.229 | 62.5 | 37.0 | 0.2 | expectancy,drawdown |
| 16 | `eh02_win_2` | EH-02 | 計測30分 | FAIL | 12 | -1.125 | 4.7 | 16.7 | 0.0 | expectancy,min_trades |
| 17 | `eh02_win_8` | EH-02 | 計測2h | FAIL | 20 | -0.900 | 7.0 | 25.0 | 0.0 | expectancy,min_trades |
| 18 | `eh02_no_mom` | EH-02 | 同方向確認なし | FAIL | 23 | -0.120 | 4.5 | 43.5 | -0.0 | expectancy,min_trades |
| 19 | `eh02_trail_1p5` | EH-02 | トレール1.5ATR | FAIL | 14 | -0.349 | 2.4 | 35.7 | 0.0 | expectancy,min_trades |
| 20 | `eh02_long_only` | EH-02 | ロングのみ | FAIL | 8 | -0.988 | 2.8 | 25.0 | 0.0 | expectancy,min_trades |
| 21 | `eh03_base` | EH-03 | プレミアム上位10%+失速 | FAIL | 674 | -0.038 | 23.9 | 43.0 | -2.8 | expectancy,drawdown |
| 22 | `eh03_both_sides` | EH-03 | 両側 | FAIL | 1094 | -0.148 | 72.6 | 39.0 | -0.8 | expectancy,drawdown |
| 23 | `eh03_ctrl_no_stall` | EH-03 | 対照: 失速確認なし | FAIL | 684 | -0.028 | 21.9 | 43.6 | -2.9 | expectancy,drawdown |
| 24 | `eh03_rank_0p95` | EH-03 | 上位5% | PASS | 430 | 0.024 | 7.9 | 45.8 | -1.9 | — |
| 25 | `eh03_rank_0p80` | EH-03 | 上位20% | FAIL | 1006 | -0.045 | 35.1 | 42.5 | -4.1 | expectancy,drawdown |
| 26 | `eh03_win_10d` | EH-03 | ランク窓10日 | FAIL | 721 | -0.056 | 27.3 | 42.4 | -3.0 | expectancy,drawdown |
| 27 | `eh03_win_60d` | EH-03 | ランク窓60日 | FAIL | 617 | -0.052 | 23.4 | 42.3 | -2.7 | expectancy,drawdown |
| 28 | `eh03_stall_24` | EH-03 | 失速6h | FAIL | 675 | -0.038 | 23.4 | 43.1 | -2.8 | expectancy,drawdown |
| 29 | `eh03_tp_3atr` | EH-03 | 利確3ATR | FAIL | 531 | -0.040 | 24.3 | 32.6 | -3.3 | expectancy,drawdown |
| 30 | `eh03_stop_2p5` | EH-03 | 損切2.5ATR | FAIL | 497 | -0.000 | 15.4 | 55.7 | -3.4 | expectancy |
| 31 | `eh04_base` | — | — | ERR | — | — | — | — | — | TypeError: Object of type complex is not JSON serializable |
| 32 | `eh04_ctrl_any` | — | — | ERR | — | — | — | — | — | TypeError: Object of type complex is not JSON serializable |
| 33 | `eh04_ctrl_expensive` | EH-04 | 対照: funding高 | FAIL | 14 | -0.567 | 3.4 | 14.3 | 0.0 | expectancy,min_trades |
| 34 | `eh04_thr_0` | EH-04 | 閾値0（受取のみ） | FAIL | 1089 | -0.105 | 56.5 | 22.2 | -3.2 | expectancy,drawdown |
| 35 | `eh04_thr_0p03` | — | — | ERR | — | — | — | — | — | TypeError: Object of type complex is not JSON serializable |
| 36 | `eh04_trend_2d` | EH-04 | トレンド2日 | FAIL | 1621 | -0.112 | 90.2 | 24.5 | 0.5 | expectancy,drawdown |
| 37 | `eh04_trend_10d` | EH-04 | トレンド10日 | FAIL | 1913 | -0.105 | 101.7 | 21.5 | 0.0 | expectancy,drawdown |
| 38 | `eh04_exit_24` | EH-04 | 構造退出24h | FAIL | 1369 | -0.133 | 86.7 | 26.6 | 0.2 | expectancy,drawdown |
| 39 | `eh04_trail_4` | EH-04 | トレール4ATR | FAIL | 1404 | -0.094 | 72.6 | 19.0 | 0.1 | expectancy,drawdown |
| 40 | `eh04_long_only` | EH-04 | ロングのみ | FAIL | 970 | -0.148 | 67.6 | 22.3 | 3.1 | expectancy,drawdown |
| 41 | `eh05_base` | EH-05 | OI上位10%+高値更新失敗 | FAIL | 116 | -0.002 | 3.4 | 44.8 | -0.6 | expectancy |
| 42 | `eh05_both_sides` | EH-05 | 両側 | FAIL | 220 | -0.089 | 10.6 | 41.8 | -0.6 | expectancy |
| 43 | `eh05_ctrl_no_oi` | EH-05 | 対照: OI条件なし | FAIL | 496 | -0.069 | 19.5 | 42.9 | -2.2 | expectancy |
| 44 | `eh05_ctrl_no_tt` | EH-05 | 対照: 上位比なし | FAIL | 274 | -0.072 | 11.9 | 41.6 | -0.9 | expectancy |
| 45 | `eh05_rank_0p95` | EH-05 | OI上位5% | FAIL | 76 | 0.001 | 2.9 | 44.7 | -0.3 | min_trades |
| 46 | `eh05_rank_0p80` | EH-05 | OI上位20% | FAIL | 201 | -0.027 | 6.0 | 43.8 | -1.0 | expectancy |
| 47 | `eh05_win_10d` | EH-05 | OIランク窓10日 | FAIL | 114 | -0.038 | 5.6 | 44.7 | -0.5 | expectancy |
| 48 | `eh05_stall_24` | EH-05 | 失速6h | PASS | 121 | 0.020 | 3.4 | 45.5 | -0.6 | — |
| 49 | `eh05_count_ratio` | EH-05 | 上位比=口座数版 | FAIL | 90 | 0.097 | 2.1 | 50.0 | -0.4 | min_trades |
| 50 | `eh05_tp_3atr` | EH-05 | 利確3ATR | FAIL | 94 | 0.054 | 3.7 | 37.2 | -0.7 | min_trades |
| 51 | `eh06_base` | EH-06 | 個人-上位 乖離1.0σ | FAIL | 1187 | -0.070 | 51.0 | 42.9 | 0.9 | expectancy,drawdown |
| 52 | `eh06_ctrl_follow_retail` | EH-06 | 対照: 個人側に付く | FAIL | 1220 | -0.083 | 54.6 | 41.4 | -0.8 | expectancy,drawdown |
| 53 | `eh06_thr_1p5` | EH-06 | 乖離1.5σ | FAIL | 752 | -0.072 | 33.2 | 43.6 | 0.7 | expectancy,drawdown |
| 54 | `eh06_thr_0p5` | EH-06 | 乖離0.5σ | FAIL | 1676 | -0.065 | 67.5 | 43.5 | 1.0 | expectancy,drawdown |
| 55 | `eh06_win_10d` | EH-06 | 基準窓10日 | FAIL | 1324 | -0.077 | 59.2 | 44.1 | 1.2 | expectancy,drawdown |
| 56 | `eh06_win_60d` | EH-06 | 基準窓60日 | FAIL | 1176 | -0.088 | 57.3 | 42.1 | 1.1 | expectancy,drawdown |
| 57 | `eh06_count_ratio` | EH-06 | 上位比=口座数版 | FAIL | 3 | 0.599 | 0.6 | 33.3 | 0.1 | min_trades |
| 58 | `eh06_tp_3atr` | EH-06 | 利確3ATR | FAIL | 773 | -0.069 | 34.9 | 33.5 | 0.9 | expectancy,drawdown |
| 59 | `eh06_stop_2p5` | EH-06 | 損切2.5ATR | FAIL | 754 | -0.102 | 41.5 | 54.0 | 0.8 | expectancy,drawdown |
| 60 | `eh06_short_only` | EH-06 | ショートのみ | FAIL | 699 | -0.052 | 24.1 | 43.9 | -1.3 | expectancy,drawdown |
| 61 | `eh07_base` | EH-07 | OI急減1%/2h+大足 | FAIL | 92 | 0.076 | 3.1 | 46.7 | 0.0 | min_trades |
| 62 | `eh07_ctrl_fade` | EH-07 | 対照: ショックをフェード | FAIL | 93 | -0.268 | 10.9 | 36.6 | -0.0 | expectancy,min_trades |
| 63 | `eh07_thr_2p0` | EH-07 | OI急減2% | FAIL | 30 | 0.331 | 1.2 | 53.3 | 0.0 | min_trades |
| 64 | `eh07_thr_0p5` | EH-07 | OI急減0.5% | FAIL | 147 | -0.001 | 5.9 | 44.9 | 0.0 | expectancy |
| 65 | `eh07_range_3` | EH-07 | 値幅3ATR | FAIL | 32 | 0.221 | 1.9 | 50.0 | -0.0 | min_trades |
| 66 | `eh07_range_1p5` | EH-07 | 値幅1.5ATR | PASS | 162 | 0.002 | 7.1 | 45.7 | -0.1 | — |
| 67 | `eh07_delay_0` | EH-07 | 遅延なし | FAIL | 99 | 0.092 | 3.0 | 51.5 | 0.1 | min_trades |
| 68 | `eh07_delay_8` | EH-07 | 遅延2h | FAIL | 80 | -0.066 | 5.5 | 45.0 | 0.2 | expectancy,min_trades |
| 69 | `eh07_pre_48h` | EH-07 | 元方向48h | FAIL | 92 | 0.204 | 2.3 | 51.1 | 0.0 | min_trades |
| 70 | `eh07_flushwin_16` | EH-07 | OI計測4h | FAIL | 99 | 0.022 | 3.1 | 44.4 | 0.0 | min_trades |
| 71 | `eh08_base` | EH-08 | 圧縮+OI増1%/24h | PASS | 294 | 0.002 | 14.3 | 29.6 | 0.2 | — |
| 72 | `eh08_ctrl_no_build` | EH-08 | 対照: OI増なし | FAIL | 448 | -0.024 | 18.8 | 30.1 | 0.2 | expectancy |
| 73 | `eh08_build_2p0` | EH-08 | OI増2% | FAIL | 207 | -0.012 | 11.6 | 30.9 | 0.2 | expectancy |
| 74 | `eh08_build_0p5` | EH-08 | OI増0.5% | PASS | 330 | 0.003 | 14.2 | 29.4 | 0.2 | — |
| 75 | `eh08_quiet_0p2` | EH-08 | 圧縮下位20% | PASS | 204 | 0.074 | 7.4 | 33.8 | 0.1 | — |
| 76 | `eh08_quiet_0p4` | EH-08 | 圧縮下位40% | PASS | 343 | 0.019 | 12.6 | 32.4 | 0.2 | — |
| 77 | `eh08_win_48` | EH-08 | 圧縮窓12h | FAIL | 319 | -0.082 | 18.0 | 25.4 | 0.1 | expectancy |
| 78 | `eh08_win_192` | EH-08 | 圧縮窓48h | PASS | 257 | 0.044 | 8.7 | 30.7 | 0.1 | — |
| 79 | `eh08_trail_4` | EH-08 | トレール4ATR | PASS | 267 | 0.038 | 11.6 | 27.7 | 0.2 | — |
| 80 | `eh08_long_only` | EH-08 | ロングのみ | FAIL | 163 | -0.068 | 10.3 | 26.4 | 0.7 | expectancy |
| 81 | `eh09_base` | EH-09 | 高値更新+成行買い減衰 | FAIL | 538 | -0.024 | 14.9 | 44.1 | -0.4 | expectancy |
| 82 | `eh09_ctrl_confirm` | EH-09 | 対照: 成行と同方向 | FAIL | 682 | -0.089 | 33.2 | 43.5 | -0.0 | expectancy,drawdown |
| 83 | `eh09_win_8` | EH-09 | 成行計測2h | FAIL | 513 | -0.055 | 21.3 | 43.9 | -0.0 | expectancy,drawdown |
| 84 | `eh09_win_32` | EH-09 | 成行計測8h | FAIL | 501 | -0.017 | 11.9 | 44.9 | -0.4 | expectancy |
| 85 | `eh09_slope_0p05` | EH-09 | 傾き閾値0.05 | FAIL | 372 | -0.017 | 9.2 | 43.8 | -0.3 | expectancy |
| 86 | `eh09_slope_0p15` | EH-09 | 傾き閾値0.15 | FAIL | 139 | -0.026 | 3.5 | 48.2 | -0.1 | expectancy |
| 87 | `eh09_tp_3atr` | EH-09 | 利確3ATR | PASS | 497 | 0.050 | 5.6 | 36.0 | -0.4 | — |
| 88 | `eh09_stop_2p5` | EH-09 | 損切2.5ATR | FAIL | 451 | -0.077 | 20.3 | 54.8 | -0.4 | expectancy,drawdown |
| 89 | `eh09_short_only` | EH-09 | ショートのみ | PASS | 307 | 0.030 | 3.7 | 47.6 | -0.9 | — |
| 90 | `eh09_trail_2p5` | EH-09 | トレール併用 | FAIL | 471 | -0.094 | 22.7 | 29.5 | -0.3 | expectancy,drawdown |
| 91 | `eh10_base` | EH-10 | funding高→平常(≤0.01%)+構造維持 | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 92 | `eh10_ctrl_no_reset` | — | — | ERR | — | — | — | — | — | TypeError: Object of type complex is not JSON serializable |
| 93 | `eh10_high_0p05` | EH-10 | 事前高0.05% | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 94 | `eh10_high_0p02` | EH-10 | 事前高0.02% | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 95 | `eh10_now_0p02` | EH-10 | 平常0.02%まで許容 | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 96 | `eh10_win_2d` | EH-10 | 参照窓2日 | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 97 | `eh10_win_5d` | EH-10 | 参照窓5日 | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 98 | `eh10_trend_2d` | EH-10 | トレンド2日 | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 99 | `eh10_trail_4` | EH-10 | トレール4ATR | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |
| 100 | `eh10_long_only` | EH-10 | ロングのみ | FAIL | 0 | 0.000 | 0.0 | 0.0 | 0.0 | expectancy,min_trades |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-01

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh01_base` | 313 | -0.018 | 11.6 |
| 対照 | `eh01_ctrl_no_oi` | 614 | -0.099 | 34.5 |
| 対照 | `eh01_ctrl_oi_down` | 247 | -0.073 | 13.9 |

本命−対照のEV差: `eh01_ctrl_no_oi` 比 +0.080 / `eh01_ctrl_oi_down` 比 +0.054

n≥30で最良EV: `eh01_brk_192` EV=0.008 n=227

### EH-02

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh02_base` | 14 | -0.533 | 3.4 |
| 対照 | `eh02_ctrl_perp_lead` | 16 | -0.952 | 5.3 |

本命−対照のEV差: `eh02_ctrl_perp_lead` 比 +0.419

n≥30で最良EV: `eh02_thr_0p02` EV=-0.229 n=673

### EH-03

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh03_base` | 674 | -0.038 | 23.9 |
| 対照 | `eh03_ctrl_no_stall` | 684 | -0.028 | 21.9 |

本命−対照のEV差: `eh03_ctrl_no_stall` 比 -0.010

n≥30で最良EV: `eh03_rank_0p95` EV=0.024 n=430

### EH-04

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh04_ctrl_expensive` | 14 | -0.567 | 3.4 |

n≥30で最良EV: `eh04_trail_4` EV=-0.094 n=1404

### EH-05

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh05_base` | 116 | -0.002 | 3.4 |
| 対照 | `eh05_ctrl_no_oi` | 496 | -0.069 | 19.5 |
| 対照 | `eh05_ctrl_no_tt` | 274 | -0.072 | 11.9 |

本命−対照のEV差: `eh05_ctrl_no_oi` 比 +0.067 / `eh05_ctrl_no_tt` 比 +0.070

n≥30で最良EV: `eh05_count_ratio` EV=0.097 n=90

### EH-06

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06_base` | 1187 | -0.070 | 51.0 |
| 対照 | `eh06_ctrl_follow_retail` | 1220 | -0.083 | 54.6 |

本命−対照のEV差: `eh06_ctrl_follow_retail` 比 +0.013

n≥30で最良EV: `eh06_short_only` EV=-0.052 n=699

### EH-07

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh07_base` | 92 | 0.076 | 3.1 |
| 対照 | `eh07_ctrl_fade` | 93 | -0.268 | 10.9 |

本命−対照のEV差: `eh07_ctrl_fade` 比 +0.344

n≥30で最良EV: `eh07_thr_2p0` EV=0.331 n=30

### EH-08

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh08_base` | 294 | 0.002 | 14.3 |
| 対照 | `eh08_ctrl_no_build` | 448 | -0.024 | 18.8 |

本命−対照のEV差: `eh08_ctrl_no_build` 比 +0.025

n≥30で最良EV: `eh08_quiet_0p2` EV=0.074 n=204

### EH-09

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09_base` | 538 | -0.024 | 14.9 |
| 対照 | `eh09_ctrl_confirm` | 682 | -0.089 | 33.2 |

本命−対照のEV差: `eh09_ctrl_confirm` 比 +0.065

n≥30で最良EV: `eh09_tp_3atr` EV=0.050 n=497

### EH-10

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh10_base` | 0 | 0.000 | 0.0 |

n≥30で最良EV: `eh10_base` EV=0.000 n=0

## PASS一覧

- `eh08_quiet_0p2` (EH-08) EV=0.074 n=204 DD=7.4%
- `eh09_tp_3atr` (EH-09) EV=0.050 n=497 DD=5.6%
- `eh08_win_192` (EH-08) EV=0.044 n=257 DD=8.7%
- `eh08_trail_4` (EH-08) EV=0.038 n=267 DD=11.6%
- `eh09_short_only` (EH-09) EV=0.030 n=307 DD=3.7%
- `eh03_rank_0p95` (EH-03) EV=0.024 n=430 DD=7.9%
- `eh05_stall_24` (EH-05) EV=0.020 n=121 DD=3.4%
- `eh08_quiet_0p4` (EH-08) EV=0.019 n=343 DD=12.6%
- `eh01_brk_192` (EH-01) EV=0.008 n=227 DD=9.2%
- `eh08_build_0p5` (EH-08) EV=0.003 n=330 DD=14.2%
- `eh07_range_1p5` (EH-07) EV=0.002 n=162 DD=7.1%
- `eh08_base` (EH-08) EV=0.002 n=294 DD=14.3%
