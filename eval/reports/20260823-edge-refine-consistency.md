# EH-01R / EH-07R / EH-02R — 改良ノブの一貫性

各ノブを **自分の基準線（base）との差** で評価する。Set B と Set C で
同じ向きに動いたノブだけが持ち越す価値がある。符号が反転したものは期間依存。

- n<30 は判定不能
- ΔEV は base に対する1トレードあたりの改善（＋が良い）

## EH-01R

基準線 `eh01r_base`: Set B n=235 EV=-0.097 / Set C n=313 EV=-0.018

| ノブ | ΔEV(B) | ΔEV(C) | 判定 |
|------|--------|--------|------|
| `eh01r_trail_4` | +0.009 | +0.011 | **改善（両期間）** |
| `eh01r_trail_off` | +0.002 | +0.058 | **改善（両期間）** |
| `eh01r_trail_1p5` | -0.120 | -0.116 | 悪化（両期間） |
| `eh01r_brk192_trail_4` | +0.161 | -0.004 | 不安定 |
| `eh01r_entry_confirm` | +0.110 | -0.050 | 不安定 |
| `eh01r_brk192_retest` | +0.103 | -0.017 | 不安定 |
| `eh01r_tp_3atr` | +0.095 | -0.026 | 不安定 |
| `eh01r_entry_retest_24` | +0.054 | -0.076 | 不安定 |
| `eh01r_retest_stop_2p5` | +0.051 | -0.101 | 不安定 |
| `eh01r_stop_1p0` | +0.046 | -0.033 | 不安定 |
| `eh01r_retest_trail_4` | +0.046 | -0.061 | 不安定 |
| `eh01r_exit_24` | +0.037 | -0.029 | 不安定 |
| `eh01r_entry_delay_4` | +0.034 | -0.102 | 不安定 |
| `eh01r_stop_2p5` | +0.026 | -0.014 | 不安定 |
| `eh01r_entry_retest` | +0.024 | -0.069 | 不安定 |
| `eh01r_stop_3p5` | +0.024 | -0.021 | 不安定 |
| `eh01r_exit_192` | +0.015 | -0.021 | 不安定 |
| `eh01r_exit_off` | +0.015 | -0.021 | 不安定 |
| `eh01r_entry_retest_tight` | +0.015 | -0.083 | 不安定 |
| `eh01r_tp_6atr` | +0.013 | -0.002 | 不安定 |
| `eh01r_entry_delay_8` | +0.009 | -0.121 | 不安定 |
| `eh01r_exit_96` | +0.008 | -0.020 | 不安定 |
| `eh01r_trail_6` | -0.008 | +0.022 | 不安定 |

両期間で改善: `eh01r_trail_4`, `eh01r_trail_off`

両期間で悪化: `eh01r_trail_1p5`

## EH-07R

基準線 `eh07r_base`: Set B n=62 EV=-0.073 / Set C n=92 EV=+0.076

| ノブ | ΔEV(B) | ΔEV(C) | 判定 |
|------|--------|--------|------|
| `eh07r_reclaim_stop_2p5` | +0.038 | +0.147 | **改善（両期間）** |
| `eh07r_hifreq_rebuild` | -0.013 | -0.152 | 悪化（両期間） |
| `eh07r_hifreq_delay` | -0.022 | -0.088 | 悪化（両期間） |
| `eh07r_hifreq_reclaim` | -0.023 | -0.135 | 悪化（両期間） |
| `eh07r_reclaim_thr0p5` | -0.023 | -0.151 | 悪化（両期間） |
| `eh07r_oi_rebuild_trail` | -0.033 | -0.300 | 悪化（両期間） |
| `eh07r_oi_rebuild_thr0p5` | -0.052 | -0.154 | 悪化（両期間） |
| `eh07r_oi_rebuild_1p0` | -0.059 | -0.224 | 悪化（両期間） |
| `eh07r_reclaim_range1p5` | -0.060 | -0.307 | 悪化（両期間） |
| `eh07r_oi_rebuild` | -0.083 | -0.047 | 悪化（両期間） |
| `eh07r_reclaim_pre48` | +0.388 | -0.153 | 不安定 |
| `eh07r_oi_rebuild_pre48` | +0.298 | -0.018 | 不安定 |
| `eh07r_reclaim_trail` | +0.181 | -0.475 | 不安定 |
| `eh07r_stabilize_trail` | +0.165 | -0.291 | 不安定 |
| `eh07r_reclaim_w96` | +0.039 | -0.178 | 不安定 |
| `eh07r_stabilize` | +0.030 | -0.083 | 不安定 |
| `eh07r_stabilize_w96` | +0.030 | -0.083 | 不安定 |
| `eh07r_reclaim_tp3` | +0.028 | -0.403 | 不安定 |
| `eh07r_reclaim` | +0.020 | -0.231 | 不安定 |
| `eh07r_oi_rebuild_w96` | +0.009 | -0.012 | 不安定 |

両期間で改善: `eh07r_reclaim_stop_2p5`

両期間で悪化: `eh07r_hifreq_rebuild`, `eh07r_hifreq_delay`, `eh07r_hifreq_reclaim`, `eh07r_reclaim_thr0p5`, `eh07r_oi_rebuild_trail`, `eh07r_oi_rebuild_thr0p5`, `eh07r_oi_rebuild_1p0`, `eh07r_reclaim_range1p5`, `eh07r_oi_rebuild`

## EH-02R

基準線 `eh02r_base`: Set B n=309 EV=-0.125 / Set C n=525 EV=-0.153

| ノブ | ΔEV(B) | ΔEV(C) | 判定 |
|------|--------|--------|------|
| `eh02r_trigger_only` | +0.066 | +0.013 | **改善（両期間）** |
| `eh02r_trail_4` | +0.058 | +0.010 | **改善（両期間）** |
| `eh02r_ctrl_no_gate` | +0.018 | +0.044 | **改善（両期間）** |
| `eh02r_brk_16` | +0.009 | +0.001 | **改善（両期間）** |
| `eh02r_spread` | +0.003 | +0.002 | **改善（両期間）** |
| `eh02r_zwin_10d` | -0.028 | -0.007 | 悪化（両期間） |
| `eh02r_long_only` | +0.094 | -0.068 | 不安定 |
| `eh02r_z_0p25` | +0.034 | -0.013 | 不安定 |
| `eh02r_win_16` | -0.024 | +0.079 | 不安定 |
| `eh02r_win_2` | -0.027 | +0.041 | 不安定 |
| `eh02r_cum_16` | -0.028 | +0.078 | 不安定 |
| `eh02r_spread_16` | -0.036 | +0.084 | 不安定 |
| `eh02r_ctrl_perp_gate` | -0.078 | +0.033 | 不安定 |
| `eh02r_z_1p5` | -0.096 | +0.020 | 不安定 |
| `eh02r_brk_96` | -0.099 | +0.007 | 不安定 |
| `eh02r_z_1p0` | -0.120 | +0.013 | 不安定 |
| `eh02r_cum` | +0.000 | +0.001 | 不安定 |

両期間で改善: `eh02r_trigger_only`, `eh02r_trail_4`, `eh02r_ctrl_no_gate`, `eh02r_brk_16`, `eh02r_spread`

両期間で悪化: `eh02r_zwin_10d`

## 両期間で符号がプラスだった変種（絶対値）

| logic | nB | EV(B) | nC | EV(C) | ゲート |
|-------|----|-------|----|-------|--------|
| `eh07r_oi_rebuild_pre48` | 59 | +0.225 | 79 | +0.058 | — |
