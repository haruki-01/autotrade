# SH-01 slow pack — Set C

銘柄: BTCUSDT  ／  ロジック 14 本  ／  min_trades=100（全銘柄合計）, max_dd=20.0%, risk=3.0 USDT/trade, 最低 50 エントリー/月

実行環境: python 3.12.3 / pandas 2.2.3 / numpy 2.4.4 / lock eval_v3_btc.lock.yaml@e7bcbe449cbb

| logic | ノブ | n | 月あたり | EV | 勝率 | DD | 総リターン | 判定 | 落ちた条件 |
|-------|------|---|---------|----|------|----|-----------|------|-----------|
| `sh01n_center` | 中心: 利確4ATR | 57 | 1.8 | +0.456 | 35.1% | 7.6% | +8.7% | FAIL | min_trades, trade_rate |
| `sh01n_tp_2` | 利確2ATR | 76 | 2.4 | +0.064 | 44.7% | 10.1% | +1.6% | FAIL | min_trades, trade_rate |
| `sh01n_tp_3` | 利確3ATR | 63 | 2.0 | +0.571 | 41.3% | 6.6% | +12.0% | FAIL | min_trades, trade_rate |
| `sh01n_tp_5` | 利確5ATR | 55 | 1.7 | +0.105 | 29.1% | 12.0% | +1.9% | FAIL | min_trades, trade_rate |
| `sh01n_tp_6` | 利確6ATR | 53 | 1.7 | +0.437 | 28.3% | 11.6% | +7.7% | FAIL | min_trades, trade_rate |
| `sh01n_tp_8` | 利確8ATR | 47 | 1.5 | +0.554 | 27.7% | 11.5% | +8.7% | FAIL | min_trades, trade_rate |
| `sh01n_entry_15d` | 入口15日 | 65 | 2.1 | +0.111 | 32.3% | 10.2% | +2.4% | FAIL | min_trades, trade_rate |
| `sh01n_entry_25d` | 入口25日 | 49 | 1.5 | +0.416 | 32.7% | 6.0% | +6.8% | FAIL | min_trades, trade_rate |
| `sh01n_entry_30d` | 入口30日 | 48 | 1.5 | +0.092 | 29.2% | 7.1% | +1.5% | FAIL | min_trades, trade_rate |
| `sh01n_exit_7d` | 退出7日 | 58 | 1.8 | +0.277 | 34.5% | 9.7% | +5.4% | FAIL | min_trades, trade_rate |
| `sh01n_exit_15d` | 退出15日 | 57 | 1.8 | +0.431 | 33.3% | 9.1% | +8.2% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p25` | 損切1.25日足ATR | 59 | 1.9 | +0.718 | 33.9% | 8.3% | +14.1% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p75` | 損切1.75日足ATR | 55 | 1.7 | +0.344 | 36.4% | 8.7% | +6.3% | FAIL | min_trades, trade_rate |
| `sh01n_stop_2p0` | 損切2.0日足ATR | 54 | 1.7 | +0.373 | 38.9% | 8.4% | +6.7% | FAIL | min_trades, trade_rate |
