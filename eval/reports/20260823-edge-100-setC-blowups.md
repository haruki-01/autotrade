# EH-01〜EH-10 — 検証100サイクル（Set C）

実行UTC: 2026-08-23T02:40:41Z  
データ: binance_vision / 現物OHLCV + Binance USDⓈ-M の OI・funding・basis・成行比率  
コスト: eval_v1.1 lock（fee 0.055%/side, slip 0.02%/side）に **funding 実費** を追加

## 方針

- 1ロジック＝ノブ1点。各ファミリーに **対照（フィルタ除去／符号反転）** を含める
- 合否は差の読み取りに使う。単体のEVだけでは採用しない
- `min_trades=100` は Set B 1年合計。足は15分

## サマリー

- Gate PASS: **0 / 5**

| # | logic | 仮説 | ノブ | Gate | n | EV$ | DD% | 勝率 | funding$ | 不合格要因 |
|---|-------|------|------|------|---|-----|-----|------|----------|------------|
| 1 | `eh02_ctrl_no_lead` | EH-02 | 対照: 乖離なし | FAIL | 2124 | -0.097 | 105.2 | 41.7 | 0.2 | expectancy,drawdown |
| 2 | `eh04_base` | EH-04 | 4日トレンド+funding安 | FAIL | 1804 | -0.123 | 106.4 | 22.1 | 0.2 | expectancy,drawdown |
| 3 | `eh04_ctrl_any` | EH-04 | 対照: fundingフィルタなし | FAIL | 1812 | -0.123 | 106.7 | 22.1 | 0.2 | expectancy,drawdown |
| 4 | `eh04_thr_0p03` | EH-04 | 閾値0.03% | FAIL | 1812 | -0.123 | 106.7 | 22.1 | 0.2 | expectancy,drawdown |
| 5 | `eh10_ctrl_no_reset` | EH-10 | 対照: リセット条件なし | FAIL | 1812 | -0.123 | 106.7 | 22.1 | 0.2 | expectancy,drawdown |

## 仮説ごとの読み取り（本命 vs 対照）

### EH-02

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh02_ctrl_no_lead` | 2124 | -0.097 | 105.2 |

n≥30で最良EV: `eh02_ctrl_no_lead` EV=-0.097 n=2124

### EH-04

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 本命 | `eh04_base` | 1804 | -0.123 | 106.4 |
| 対照 | `eh04_ctrl_any` | 1812 | -0.123 | 106.7 |

本命−対照のEV差: `eh04_ctrl_any` 比 -0.000

n≥30で最良EV: `eh04_ctrl_any` EV=-0.123 n=1812

### EH-10

| 役割 | logic | n | EV$ | DD% |
|------|-------|---|-----|-----|
| 対照 | `eh10_ctrl_no_reset` | 1812 | -0.123 | 106.7 |

n≥30で最良EV: `eh10_ctrl_no_reset` EV=-0.123 n=1812

## PASS一覧

- なし
