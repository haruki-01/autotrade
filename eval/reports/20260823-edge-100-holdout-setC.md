# EH-01〜EH-10 — 検証100サイクル（Set C）

実行UTC: 2026-08-23T02:34:06Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **2 / 15**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh01_long_only` | EH-01 | ロングのみ | FAIL | 191 | -0.129 | 14.2 | 28.3 | 0.8 | expectancy |
| 2 | `eh09_slope_0p05` | EH-09 | 傾き閾値0.05 | FAIL | 372 | -0.017 | 9.2 | 43.8 | -0.3 | expectancy |
| 3 | `eh08_long_only` | EH-08 | ロングのみ | FAIL | 163 | -0.068 | 10.3 | 26.4 | 0.7 | expectancy |
| 4 | `eh08_ctrl_no_build` | EH-08 | 対照: OI増なし | FAIL | 448 | -0.024 | 18.8 | 30.1 | 0.2 | expectancy |
| 5 | `eh09_win_8` | EH-09 | 成行計測2h | FAIL | 513 | -0.055 | 21.3 | 43.9 | -0.0 | expectancy,drawdown |
| 6 | `eh09_trail_2p5` | EH-09 | トレール併用 | FAIL | 471 | -0.094 | 22.7 | 29.5 | -0.3 | expectancy,drawdown |
| 7 | `eh01_brk_192` | EH-01 | 突破48h | PASS | 227 | 0.008 | 9.2 | 30.0 | 0.2 | — |
| 8 | `eh09_base` | EH-09 | 高値更新+成行買い減衰 | FAIL | 538 | -0.024 | 14.9 | 44.1 | -0.4 | expectancy |
| 9 | `eh08_trail_4` | EH-08 | トレール4ATR | PASS | 267 | 0.038 | 11.6 | 27.7 | 0.2 | — |
| 10 | `eh06_win_10d` | EH-06 | 基準窓10日 | FAIL | 1324 | -0.077 | 59.2 | 44.1 | 1.2 | expectancy,drawdown |
| 11 | `eh09_win_32` | EH-09 | 成行計測8h | FAIL | 501 | -0.017 | 11.9 | 44.9 | -0.4 | expectancy |
| 12 | `eh02_base` | EH-02 | 現物先行1h+0.05% | FAIL | 14 | -0.533 | 3.4 | 35.7 | 0.0 | expectancy,min_trades |
| 13 | `eh02_win_8` | EH-02 | 計測2h | FAIL | 20 | -0.900 | 7.0 | 25.0 | 0.0 | expectancy,min_trades |
| 14 | `eh01_base` | EH-01 | 24h突破+OI増0.5%/4h | FAIL | 313 | -0.018 | 11.6 | 30.7 | 0.2 | expectancy |
| 15 | `eh06_base` | EH-06 | 個人-上位 乖離1.0σ | FAIL | 1187 | -0.070 | 51.0 | 42.9 | 0.9 | expectancy,drawdown |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-01

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh01_base` | 313 | -0.018 | 11.6 |

n≥30で最良EV: `eh01_brk_192` EV=0.008 n=227

### EH-02

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh02_base` | 14 | -0.533 | 3.4 |

n≥30で最良EV: `eh02_base` EV=-0.533 n=14

### EH-06

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh06_base` | 1187 | -0.070 | 51.0 |

n≥30で最良EV: `eh06_base` EV=-0.070 n=1187

### EH-08

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh08_ctrl_no_build` | 448 | -0.024 | 18.8 |

n≥30で最良EV: `eh08_trail_4` EV=0.038 n=267

### EH-09

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh09_base` | 538 | -0.024 | 14.9 |

n≥30で最良EV: `eh09_win_32` EV=-0.017 n=501

## PASS一覧

- `eh08_trail_4` (EH-08) EV=0.038 n=267 DD=11.6%
- `eh01_brk_192` (EH-01) EV=0.008 n=227 DD=9.2%
