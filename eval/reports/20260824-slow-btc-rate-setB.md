# SH-01 slow pack — Set B

銘柄: BTCUSDT  ／  ロジック 14 本  ／  min_trades=100（全銘柄合計）, max_dd=20.0%, risk=3.0 USDT/trade, 最低 50 エントリー/月

実行環境: python 3.12.3 / pandas 2.2.3 / numpy 2.4.4 / lock eval_v3_btc.lock.yaml@e7bcbe449cbb

| logic | ノブ | n | 月あたり | EV | 勝率 | DD | 総リターン | 判定 | 落ちた条件 |
|-------|------|---|---------|----|------|----|-----------|------|-----------|
| `sh01n_center` | 中心: 利確4ATR | 51 | 1.6 | +0.528 | 37.3% | 5.3% | +9.0% | FAIL | min_trades, trade_rate |
| `sh01n_tp_2` | 利確2ATR | 59 | 1.8 | -0.135 | 40.7% | 7.3% | -2.7% | FAIL | min_trades, expectancy, trade_rate |
| `sh01n_tp_3` | 利確3ATR | 56 | 1.7 | +0.430 | 39.3% | 5.5% | +8.0% | FAIL | min_trades, trade_rate |
| `sh01n_tp_5` | 利確5ATR | 48 | 1.5 | +0.651 | 35.4% | 6.5% | +10.4% | FAIL | min_trades, trade_rate |
| `sh01n_tp_6` | 利確6ATR | 44 | 1.4 | +1.037 | 38.6% | 4.8% | +15.2% | FAIL | min_trades, trade_rate |
| `sh01n_tp_8` | 利確8ATR | 39 | 1.2 | +1.445 | 43.6% | 4.7% | +18.8% | FAIL | min_trades, trade_rate |
| `sh01n_entry_15d` | 入口15日 | 56 | 1.7 | +0.492 | 33.9% | 5.0% | +9.2% | FAIL | min_trades, trade_rate |
| `sh01n_entry_25d` | 入口25日 | 46 | 1.4 | +0.309 | 37.0% | 6.0% | +4.7% | FAIL | min_trades, trade_rate |
| `sh01n_entry_30d` | 入口30日 | 44 | 1.4 | +0.090 | 36.4% | 9.8% | +1.3% | FAIL | min_trades, trade_rate |
| `sh01n_exit_7d` | 退出7日 | 52 | 1.6 | +0.525 | 36.5% | 5.0% | +9.1% | FAIL | min_trades, trade_rate |
| `sh01n_exit_15d` | 退出15日 | 50 | 1.6 | +0.529 | 36.0% | 6.3% | +8.8% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p25` | 損切1.25日足ATR | 54 | 1.7 | +0.601 | 35.2% | 6.5% | +10.8% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p75` | 損切1.75日足ATR | 49 | 1.5 | +0.700 | 40.8% | 3.6% | +11.4% | FAIL | min_trades, trade_rate |
| `sh01n_stop_2p0` | 損切2.0日足ATR | 48 | 1.5 | +0.706 | 43.8% | 3.6% | +11.3% | FAIL | min_trades, trade_rate |
