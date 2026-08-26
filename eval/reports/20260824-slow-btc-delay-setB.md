# SH-01 slow pack — Set B

銘柄: BTCUSDT  ／  ロジック 3 本  ／  min_trades=100（全銘柄合計）, max_dd=20.0%, risk=3.0 USDT/trade

実行環境: python 3.12.3 / pandas 2.2.3 / numpy 2.4.4 / lock eval_v3_btc.lock.yaml@bcc5efaffb3e

| logic | ノブ | n | EV | 勝率 | DD | 総リターン | 判定 |
|-------|------|---|----|------|----|-----------|------|
| `sh01_tp_4atr` | 利確4ATR | 51 | +0.528 | 37.3% | 5.3% | +9.0% | FAIL |
| `sh01_tp4_delay_1h` | 反証: 3期間PASS版を1時間遅らせる | 49 | +0.646 | 40.8% | 5.0% | +10.5% | FAIL |
| `sh01_tp4_delay_1d` | 反証: 3期間PASS版を1日遅らせる | 49 | +0.333 | 34.7% | 8.4% | +5.4% | FAIL |
