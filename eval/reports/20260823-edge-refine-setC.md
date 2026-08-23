# EH-01〜EH-10 — 検証100サイクル（Set C）

実行UTC: 2026-08-23T04:47:43Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **2 / 63**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh01r_base` | EH-01R | 再掲: 突破即入り/トレール2.5 | FAIL | 313 | -0.018 | 11.6 | 30.7 | 0.2 | expectancy |
| 2 | `eh01r_trail_off` | EH-01R | トレールなし（構造退出のみ） | PASS | 281 | 0.040 | 9.7 | 26.7 | 0.4 | — |
| 3 | `eh01r_trail_1p5` | EH-01R | トレール1.5ATR | FAIL | 394 | -0.134 | 26.3 | 34.8 | 0.2 | expectancy,drawdown |
| 4 | `eh01r_trail_4` | EH-01R | トレール4ATR | FAIL | 285 | -0.008 | 10.7 | 29.1 | 0.4 | expectancy |
| 5 | `eh01r_trail_6` | EH-01R | トレール6ATR | PASS | 283 | 0.004 | 9.6 | 26.9 | 0.4 | — |
| 6 | `eh01r_stop_1p0` | EH-01R | 損切1.0ATR | FAIL | 348 | -0.052 | 15.8 | 25.0 | 0.2 | expectancy |
| 7 | `eh01r_stop_2p5` | EH-01R | 損切2.5ATR | FAIL | 298 | -0.033 | 13.9 | 34.2 | 0.3 | expectancy |
| 8 | `eh01r_stop_3p5` | EH-01R | 損切3.5ATR | FAIL | 298 | -0.040 | 14.4 | 34.2 | 0.3 | expectancy |
| 9 | `eh01r_exit_24` | EH-01R | 構造退出6h | FAIL | 327 | -0.048 | 13.5 | 30.3 | 0.2 | expectancy |
| 10 | `eh01r_exit_96` | EH-01R | 構造退出24h | FAIL | 313 | -0.038 | 12.5 | 29.7 | 0.3 | expectancy |
| 11 | `eh01r_exit_192` | EH-01R | 構造退出48h | FAIL | 312 | -0.039 | 12.6 | 29.5 | 0.3 | expectancy |
| 12 | `eh01r_exit_off` | EH-01R | 構造退出なし | FAIL | 312 | -0.039 | 12.6 | 29.5 | 0.3 | expectancy |
| 13 | `eh01r_tp_3atr` | EH-01R | 利確3ATR（トレールなし） | FAIL | 401 | -0.044 | 16.3 | 35.4 | 0.3 | expectancy |
| 14 | `eh01r_tp_6atr` | EH-01R | 利確6ATR（トレールなし） | FAIL | 328 | -0.020 | 12.4 | 28.4 | 0.4 | expectancy |
| 15 | `eh01r_entry_confirm` | EH-01R | 1本後も突破維持を確認 | FAIL | 257 | -0.069 | 11.0 | 29.6 | 0.2 | expectancy |
| 16 | `eh01r_entry_delay_4` | EH-01R | 1時間待って入る | FAIL | 314 | -0.121 | 19.8 | 27.7 | 0.3 | expectancy |
| 17 | `eh01r_entry_delay_8` | EH-01R | 2時間待って入る | FAIL | 316 | -0.140 | 22.5 | 26.3 | 0.4 | expectancy,drawdown |
| 18 | `eh01r_entry_retest` | EH-01R | 突破水準への戻りで入る | FAIL | 283 | -0.088 | 15.4 | 31.8 | 0.3 | expectancy |
| 19 | `eh01r_entry_retest_tight` | EH-01R | 戻り許容0.2ATR | FAIL | 281 | -0.101 | 16.6 | 32.0 | 0.3 | expectancy |
| 20 | `eh01r_entry_retest_24` | EH-01R | 戻り待ち6hまで | FAIL | 277 | -0.095 | 15.3 | 31.4 | 0.3 | expectancy |
| 21 | `eh01r_retest_trail_4` | EH-01R | 戻り入り+トレール4 | FAIL | 257 | -0.080 | 14.6 | 27.6 | 0.4 | expectancy |
| 22 | `eh01r_retest_stop_2p5` | EH-01R | 戻り入り+損切2.5 | FAIL | 273 | -0.119 | 17.6 | 34.8 | 0.3 | expectancy |
| 23 | `eh01r_brk192_trail_4` | EH-01R | 48h突破+トレール4 | FAIL | 211 | -0.022 | 9.4 | 28.4 | 0.2 | expectancy |
| 24 | `eh01r_brk192_retest` | EH-01R | 48h突破+戻り入り | FAIL | 206 | -0.035 | 11.3 | 33.0 | 0.3 | expectancy |
| 25 | `eh07r_base` | EH-07R | 再掲: 2本遅延で入る | FAIL | 92 | 0.076 | 3.1 | 46.7 | 0.0 | min_trades |
| 26 | `eh07r_stabilize` | EH-07R | 値動きが落ち着いてから | FAIL | 83 | -0.007 | 3.3 | 45.8 | 0.0 | expectancy,min_trades |
| 27 | `eh07r_stabilize_w96` | EH-07R | 落ち着き待ち24hまで | FAIL | 83 | -0.007 | 3.3 | 45.8 | 0.0 | expectancy,min_trades |
| 28 | `eh07r_reclaim` | EH-07R | ショック前の水準を取り戻したら | FAIL | 57 | -0.155 | 5.5 | 40.4 | 0.1 | expectancy,min_trades |
| 29 | `eh07r_reclaim_w96` | EH-07R | 取り戻し24hまで | FAIL | 60 | -0.102 | 5.5 | 41.7 | 0.1 | expectancy,min_trades |
| 30 | `eh07r_oi_rebuild` | EH-07R | 建玉が積み直され始めたら | FAIL | 80 | 0.029 | 3.8 | 43.8 | 0.1 | min_trades |
| 31 | `eh07r_oi_rebuild_1p0` | EH-07R | 積み直し1.0% | FAIL | 68 | -0.147 | 8.4 | 36.8 | 0.1 | expectancy,min_trades |
| 32 | `eh07r_oi_rebuild_w96` | EH-07R | 積み直し24hまで | FAIL | 83 | 0.064 | 3.2 | 44.6 | 0.1 | min_trades |
| 33 | `eh07r_reclaim_stop_2p5` | EH-07R | 取り戻し+損切2.5 | FAIL | 56 | 0.223 | 1.7 | 66.1 | 0.1 | min_trades |
| 34 | `eh07r_reclaim_trail` | EH-07R | 取り戻し+トレール2.5 | FAIL | 55 | -0.398 | 8.2 | 23.6 | 0.0 | expectancy,min_trades |
| 35 | `eh07r_oi_rebuild_trail` | EH-07R | 積み直し+トレール2.5 | FAIL | 76 | -0.224 | 7.4 | 31.6 | 0.0 | expectancy,min_trades |
| 36 | `eh07r_stabilize_trail` | EH-07R | 落ち着き+トレール2.5 | FAIL | 81 | -0.214 | 7.5 | 29.6 | -0.0 | expectancy,min_trades |
| 37 | `eh07r_reclaim_thr0p5` | EH-07R | OI急減0.5%で取り戻し | FAIL | 95 | -0.074 | 6.2 | 46.3 | 0.1 | expectancy,min_trades |
| 38 | `eh07r_oi_rebuild_thr0p5` | EH-07R | OI急減0.5%で積み直し | FAIL | 136 | -0.077 | 9.0 | 39.7 | 0.2 | expectancy |
| 39 | `eh07r_reclaim_range1p5` | EH-07R | 値幅1.5ATRで取り戻し | FAIL | 99 | -0.230 | 9.6 | 38.4 | 0.1 | expectancy,min_trades |
| 40 | `eh07r_reclaim_pre48` | EH-07R | 元方向48h+取り戻し | FAIL | 64 | -0.077 | 5.4 | 42.2 | 0.1 | expectancy,min_trades |
| 41 | `eh07r_oi_rebuild_pre48` | EH-07R | 元方向48h+積み直し | FAIL | 79 | 0.058 | 4.1 | 44.3 | 0.1 | min_trades |
| 42 | `eh07r_reclaim_tp3` | EH-07R | 取り戻し+利確3ATR | FAIL | 57 | -0.326 | 7.1 | 26.3 | 0.2 | expectancy,min_trades |
| 43 | `eh07r_hifreq_reclaim` | EH-07R | 小さな洗浄まで拾う+取り戻し | FAIL | 396 | -0.058 | 16.1 | 45.5 | -0.0 | expectancy |
| 44 | `eh07r_hifreq_rebuild` | EH-07R | 小さな洗浄まで拾う+積み直し | FAIL | 483 | -0.076 | 22.3 | 42.7 | 0.2 | expectancy,drawdown |
| 45 | `eh07r_hifreq_delay` | EH-07R | 小さな洗浄まで拾う+2本遅延 | FAIL | 562 | -0.012 | 16.5 | 46.3 | 0.1 | expectancy |
| 46 | `eh02r_base` | EH-02R | 12h突破 × 現物先行z>0.5 | FAIL | 525 | -0.153 | 37.8 | 25.9 | -0.2 | expectancy,drawdown |
| 47 | `eh02r_ctrl_no_gate` | EH-02R | 対照: ゲートなし | FAIL | 910 | -0.109 | 51.4 | 27.4 | 0.1 | expectancy,drawdown |
| 48 | `eh02r_ctrl_perp_gate` | EH-02R | 対照: 先物先行ゲート | FAIL | 541 | -0.120 | 31.4 | 29.2 | 0.3 | expectancy,drawdown |
| 49 | `eh02r_z_1p0` | EH-02R | z>1.0 | FAIL | 341 | -0.139 | 23.8 | 26.4 | -0.4 | expectancy,drawdown |
| 50 | `eh02r_z_1p5` | EH-02R | z>1.5 | FAIL | 178 | -0.132 | 17.0 | 25.8 | -0.4 | expectancy |
| 51 | `eh02r_z_0p25` | EH-02R | z>0.25 | FAIL | 617 | -0.166 | 45.0 | 25.8 | -0.2 | expectancy,drawdown |
| 52 | `eh02r_cum` | EH-02R | 累積乖離で測る | FAIL | 524 | -0.152 | 37.5 | 26.0 | -0.2 | expectancy,drawdown |
| 53 | `eh02r_cum_16` | EH-02R | 累積乖離4h | FAIL | 502 | -0.075 | 23.0 | 28.9 | -0.2 | expectancy,drawdown |
| 54 | `eh02r_spread` | EH-02R | 価格差の変化で測る | FAIL | 523 | -0.151 | 37.3 | 26.0 | -0.2 | expectancy,drawdown |
| 55 | `eh02r_spread_16` | EH-02R | 価格差の変化4h | FAIL | 500 | -0.069 | 22.1 | 29.0 | -0.1 | expectancy,drawdown |
| 56 | `eh02r_win_16` | EH-02R | 先行計測4h | FAIL | 502 | -0.073 | 22.8 | 28.9 | -0.1 | expectancy,drawdown |
| 57 | `eh02r_win_2` | EH-02R | 先行計測30分 | FAIL | 527 | -0.112 | 30.1 | 27.9 | -0.0 | expectancy,drawdown |
| 58 | `eh02r_zwin_10d` | EH-02R | z基準10日 | FAIL | 536 | -0.160 | 39.6 | 25.7 | -0.2 | expectancy,drawdown |
| 59 | `eh02r_brk_96` | EH-02R | 24h突破に載せる | FAIL | 325 | -0.146 | 24.1 | 26.5 | -0.2 | expectancy,drawdown |
| 60 | `eh02r_brk_16` | EH-02R | 4h突破に載せる | FAIL | 775 | -0.152 | 53.1 | 27.0 | 0.0 | expectancy,drawdown |
| 61 | `eh02r_trigger_only` | EH-02R | ゲートでなく単独の引き金 | FAIL | 1474 | -0.140 | 94.6 | 23.7 | -0.4 | expectancy,drawdown |
| 62 | `eh02r_trail_4` | EH-02R | トレール4ATR | FAIL | 494 | -0.142 | 34.5 | 23.3 | -0.1 | expectancy,drawdown |
| 63 | `eh02r_long_only` | EH-02R | ロングのみ | FAIL | 258 | -0.221 | 24.4 | 23.3 | 1.1 | expectancy,drawdown |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-01R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh01r_base` | 313 | -0.018 | 11.6 |

n≥30で最良EV: `eh01r_trail_off` EV=0.040 n=281

### EH-02R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh02r_base` | 525 | -0.153 | 37.8 |
| 対照 | `eh02r_ctrl_no_gate` | 910 | -0.109 | 51.4 |
| 対照 | `eh02r_ctrl_perp_gate` | 541 | -0.120 | 31.4 |

本命−対照のEV差: `eh02r_ctrl_no_gate` 比 -0.044 / `eh02r_ctrl_perp_gate` 比 -0.033

n≥30で最良EV: `eh02r_spread_16` EV=-0.069 n=500

### EH-07R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh07r_base` | 92 | 0.076 | 3.1 |

n≥30で最良EV: `eh07r_reclaim_stop_2p5` EV=0.223 n=56

## PASS一覧

- `eh01r_trail_off` (EH-01R) EV=0.040 n=281 DD=9.7%
- `eh01r_trail_6` (EH-01R) EV=0.004 n=283 DD=9.6%
