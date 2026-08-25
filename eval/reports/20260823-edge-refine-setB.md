# EH-01〜EH-10 — 検証100サイクル（Set B）

実行UTC: 2026-08-23T04:44:17Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **3 / 63**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh01r_base` | EH-01R | 再掲: 突破即入り/トレール2.5 | FAIL | 235 | -0.097 | 16.1 | 26.4 | 1.4 | expectancy |
| 2 | `eh01r_trail_off` | EH-01R | トレールなし（構造退出のみ） | FAIL | 217 | -0.095 | 16.3 | 24.0 | 1.8 | expectancy |
| 3 | `eh01r_trail_1p5` | EH-01R | トレール1.5ATR | FAIL | 296 | -0.218 | 27.2 | 26.7 | 0.7 | expectancy,drawdown |
| 4 | `eh01r_trail_4` | EH-01R | トレール4ATR | FAIL | 219 | -0.088 | 16.0 | 24.7 | 1.6 | expectancy |
| 5 | `eh01r_trail_6` | EH-01R | トレール6ATR | FAIL | 217 | -0.105 | 16.1 | 24.0 | 1.6 | expectancy |
| 6 | `eh01r_stop_1p0` | EH-01R | 損切1.0ATR | FAIL | 254 | -0.051 | 13.1 | 22.8 | 1.2 | expectancy |
| 7 | `eh01r_stop_2p5` | EH-01R | 損切2.5ATR | FAIL | 218 | -0.071 | 13.0 | 31.7 | 1.4 | expectancy |
| 8 | `eh01r_stop_3p5` | EH-01R | 損切3.5ATR | FAIL | 213 | -0.073 | 12.9 | 32.4 | 1.3 | expectancy |
| 9 | `eh01r_exit_24` | EH-01R | 構造退出6h | FAIL | 240 | -0.060 | 13.1 | 27.5 | 1.4 | expectancy |
| 10 | `eh01r_exit_96` | EH-01R | 構造退出24h | FAIL | 232 | -0.089 | 16.1 | 27.2 | 1.5 | expectancy |
| 11 | `eh01r_exit_192` | EH-01R | 構造退出48h | FAIL | 230 | -0.082 | 15.5 | 27.8 | 1.6 | expectancy |
| 12 | `eh01r_exit_off` | EH-01R | 構造退出なし | FAIL | 230 | -0.082 | 15.5 | 27.8 | 1.6 | expectancy |
| 13 | `eh01r_tp_3atr` | EH-01R | 利確3ATR（トレールなし） | FAIL | 291 | -0.003 | 10.7 | 35.1 | 1.0 | expectancy |
| 14 | `eh01r_tp_6atr` | EH-01R | 利確6ATR（トレールなし） | FAIL | 246 | -0.084 | 15.3 | 24.8 | 1.1 | expectancy |
| 15 | `eh01r_entry_confirm` | EH-01R | 1本後も突破維持を確認 | PASS | 177 | 0.013 | 8.1 | 31.1 | 1.4 | — |
| 16 | `eh01r_entry_delay_4` | EH-01R | 1時間待って入る | FAIL | 224 | -0.063 | 11.1 | 28.6 | 1.5 | expectancy |
| 17 | `eh01r_entry_delay_8` | EH-01R | 2時間待って入る | FAIL | 226 | -0.088 | 13.5 | 28.3 | 1.6 | expectancy |
| 18 | `eh01r_entry_retest` | EH-01R | 突破水準への戻りで入る | FAIL | 195 | -0.073 | 12.3 | 30.3 | 1.3 | expectancy |
| 19 | `eh01r_entry_retest_tight` | EH-01R | 戻り許容0.2ATR | FAIL | 193 | -0.083 | 12.8 | 29.5 | 1.3 | expectancy |
| 20 | `eh01r_entry_retest_24` | EH-01R | 戻り待ち6hまで | FAIL | 187 | -0.043 | 10.6 | 31.0 | 1.3 | expectancy |
| 21 | `eh01r_retest_trail_4` | EH-01R | 戻り入り+トレール4 | FAIL | 183 | -0.052 | 11.0 | 28.4 | 1.7 | expectancy |
| 22 | `eh01r_retest_stop_2p5` | EH-01R | 戻り入り+損切2.5 | FAIL | 186 | -0.046 | 11.8 | 33.3 | 1.4 | expectancy |
| 23 | `eh01r_brk192_trail_4` | EH-01R | 48h突破+トレール4 | PASS | 145 | 0.063 | 7.9 | 29.0 | 1.6 | — |
| 24 | `eh01r_brk192_retest` | EH-01R | 48h突破+戻り入り | PASS | 131 | 0.005 | 8.5 | 32.1 | 1.3 | — |
| 25 | `eh07r_base` | EH-07R | 再掲: 2本遅延で入る | FAIL | 62 | -0.073 | 6.6 | 40.3 | 0.0 | expectancy,min_trades |
| 26 | `eh07r_stabilize` | EH-07R | 値動きが落ち着いてから | FAIL | 58 | -0.043 | 6.0 | 43.1 | 0.2 | expectancy,min_trades |
| 27 | `eh07r_stabilize_w96` | EH-07R | 落ち着き待ち24hまで | FAIL | 58 | -0.043 | 6.0 | 43.1 | 0.2 | expectancy,min_trades |
| 28 | `eh07r_reclaim` | EH-07R | ショック前の水準を取り戻したら | FAIL | 44 | -0.053 | 4.6 | 45.5 | -0.0 | expectancy,min_trades |
| 29 | `eh07r_reclaim_w96` | EH-07R | 取り戻し24hまで | FAIL | 47 | -0.034 | 4.4 | 46.8 | 0.0 | expectancy,min_trades |
| 30 | `eh07r_oi_rebuild` | EH-07R | 建玉が積み直され始めたら | FAIL | 59 | -0.157 | 7.4 | 39.0 | 0.1 | expectancy,min_trades |
| 31 | `eh07r_oi_rebuild_1p0` | EH-07R | 積み直し1.0% | FAIL | 54 | -0.132 | 6.5 | 40.7 | 0.2 | expectancy,min_trades |
| 32 | `eh07r_oi_rebuild_w96` | EH-07R | 積み直し24hまで | FAIL | 60 | -0.064 | 5.6 | 41.7 | 0.1 | expectancy,min_trades |
| 33 | `eh07r_reclaim_stop_2p5` | EH-07R | 取り戻し+損切2.5 | FAIL | 43 | -0.035 | 5.3 | 58.1 | -0.2 | expectancy,min_trades |
| 34 | `eh07r_reclaim_trail` | EH-07R | 取り戻し+トレール2.5 | FAIL | 43 | 0.108 | 4.6 | 32.6 | 0.3 | min_trades |
| 35 | `eh07r_oi_rebuild_trail` | EH-07R | 積み直し+トレール2.5 | FAIL | 57 | -0.106 | 8.1 | 28.1 | 0.4 | expectancy,min_trades |
| 36 | `eh07r_stabilize_trail` | EH-07R | 落ち着き+トレール2.5 | FAIL | 55 | 0.092 | 5.8 | 36.4 | 0.7 | min_trades |
| 37 | `eh07r_reclaim_thr0p5` | EH-07R | OI急減0.5%で取り戻し | FAIL | 66 | -0.096 | 5.2 | 45.5 | 0.3 | expectancy,min_trades |
| 38 | `eh07r_oi_rebuild_thr0p5` | EH-07R | OI急減0.5%で積み直し | FAIL | 88 | -0.126 | 9.3 | 39.8 | 0.2 | expectancy,min_trades |
| 39 | `eh07r_reclaim_range1p5` | EH-07R | 値幅1.5ATRで取り戻し | FAIL | 90 | -0.134 | 11.3 | 44.4 | -0.1 | expectancy,min_trades |
| 40 | `eh07r_reclaim_pre48` | EH-07R | 元方向48h+取り戻し | FAIL | 47 | 0.314 | 2.4 | 57.4 | 0.2 | min_trades |
| 41 | `eh07r_oi_rebuild_pre48` | EH-07R | 元方向48h+積み直し | FAIL | 59 | 0.225 | 4.2 | 52.5 | 0.1 | min_trades |
| 42 | `eh07r_reclaim_tp3` | EH-07R | 取り戻し+利確3ATR | FAIL | 43 | -0.045 | 4.8 | 37.2 | -0.1 | expectancy,min_trades |
| 43 | `eh07r_hifreq_reclaim` | EH-07R | 小さな洗浄まで拾う+取り戻し | FAIL | 276 | -0.096 | 15.2 | 43.5 | 1.2 | expectancy |
| 44 | `eh07r_hifreq_rebuild` | EH-07R | 小さな洗浄まで拾う+積み直し | FAIL | 358 | -0.086 | 20.0 | 42.5 | 0.7 | expectancy |
| 45 | `eh07r_hifreq_delay` | EH-07R | 小さな洗浄まで拾う+2本遅延 | FAIL | 378 | -0.096 | 20.3 | 42.3 | 1.2 | expectancy,drawdown |
| 46 | `eh02r_base` | EH-02R | 12h突破 × 現物先行z>0.5 | FAIL | 309 | -0.125 | 19.7 | 28.8 | 0.3 | expectancy |
| 47 | `eh02r_ctrl_no_gate` | EH-02R | 対照: ゲートなし | FAIL | 547 | -0.106 | 29.3 | 30.5 | 1.5 | expectancy,drawdown |
| 48 | `eh02r_ctrl_perp_gate` | EH-02R | 対照: 先物先行ゲート | FAIL | 331 | -0.203 | 28.9 | 27.5 | 2.1 | expectancy,drawdown |
| 49 | `eh02r_z_1p0` | EH-02R | z>1.0 | FAIL | 195 | -0.245 | 19.1 | 27.7 | -0.1 | expectancy |
| 50 | `eh02r_z_1p5` | EH-02R | z>1.5 | FAIL | 104 | -0.221 | 9.8 | 32.7 | -0.1 | expectancy |
| 51 | `eh02r_z_0p25` | EH-02R | z>0.25 | FAIL | 367 | -0.090 | 17.5 | 29.2 | 0.8 | expectancy |
| 52 | `eh02r_cum` | EH-02R | 累積乖離で測る | FAIL | 309 | -0.125 | 19.7 | 28.8 | 0.3 | expectancy |
| 53 | `eh02r_cum_16` | EH-02R | 累積乖離4h | FAIL | 293 | -0.153 | 20.9 | 28.7 | 0.5 | expectancy,drawdown |
| 54 | `eh02r_spread` | EH-02R | 価格差の変化で測る | FAIL | 308 | -0.122 | 19.4 | 28.9 | 0.3 | expectancy |
| 55 | `eh02r_spread_16` | EH-02R | 価格差の変化4h | FAIL | 295 | -0.160 | 21.7 | 28.1 | 0.4 | expectancy,drawdown |
| 56 | `eh02r_win_16` | EH-02R | 先行計測4h | FAIL | 292 | -0.148 | 20.4 | 28.8 | 0.5 | expectancy,drawdown |
| 57 | `eh02r_win_2` | EH-02R | 先行計測30分 | FAIL | 323 | -0.152 | 23.1 | 28.8 | 0.9 | expectancy,drawdown |
| 58 | `eh02r_zwin_10d` | EH-02R | z基準10日 | FAIL | 313 | -0.153 | 22.4 | 28.8 | 0.3 | expectancy,drawdown |
| 59 | `eh02r_brk_96` | EH-02R | 24h突破に載せる | FAIL | 189 | -0.223 | 17.9 | 25.9 | 0.3 | expectancy |
| 60 | `eh02r_brk_16` | EH-02R | 4h突破に載せる | FAIL | 475 | -0.116 | 27.3 | 29.9 | 1.3 | expectancy,drawdown |
| 61 | `eh02r_trigger_only` | EH-02R | ゲートでなく単独の引き金 | FAIL | 846 | -0.058 | 32.3 | 27.7 | -0.5 | expectancy,drawdown |
| 62 | `eh02r_trail_4` | EH-02R | トレール4ATR | FAIL | 285 | -0.067 | 13.9 | 28.1 | 0.5 | expectancy |
| 63 | `eh02r_long_only` | EH-02R | ロングのみ | FAIL | 153 | -0.030 | 5.7 | 30.7 | 1.9 | expectancy |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-01R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh01r_base` | 235 | -0.097 | 16.1 |

n≥30で最良EV: `eh01r_brk192_trail_4` EV=0.063 n=145

### EH-02R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh02r_base` | 309 | -0.125 | 19.7 |
| 対照 | `eh02r_ctrl_no_gate` | 547 | -0.106 | 29.3 |
| 対照 | `eh02r_ctrl_perp_gate` | 331 | -0.203 | 28.9 |

本命−対照のEV差: `eh02r_ctrl_no_gate` 比 -0.018 / `eh02r_ctrl_perp_gate` 比 +0.078

n≥30で最良EV: `eh02r_long_only` EV=-0.030 n=153

### EH-07R

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh07r_base` | 62 | -0.073 | 6.6 |

n≥30で最良EV: `eh07r_reclaim_pre48` EV=0.314 n=47

## PASS一覧

- `eh01r_brk192_trail_4` (EH-01R) EV=0.063 n=145 DD=7.9%
- `eh01r_entry_confirm` (EH-01R) EV=0.013 n=177 DD=8.1%
- `eh01r_brk192_retest` (EH-01R) EV=0.005 n=131 DD=8.5%
